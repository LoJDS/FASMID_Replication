from __future__ import annotations

import math
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Callable

import numpy as np

from .objective import ObjectiveEvaluation
from .persistence import HistoryWriter, save_best


@dataclass(frozen=True)
class CMAESResult:
    best_theta: np.ndarray
    best_log_post: float
    best_simulated_targets: dict[str, float] | None
    evaluations: int


def reflect_unit(x: np.ndarray) -> np.ndarray:
    y = np.mod(x, 2.0)
    return np.where(y <= 1.0, y, 2.0 - y)


def run_cmaes(
    *,
    param_names: list[str],
    lo: np.ndarray,
    hi: np.ndarray,
    max_evals: int,
    sigma0: float,
    popsize: int,
    restarts: int,
    seed: int,
    evaluate: Callable[[np.ndarray, str], ObjectiveEvaluation],
    history_writer: HistoryWriter,
    best_path,
    workers: int = 1,
) -> CMAESResult:
    d = len(param_names)
    span = hi - lo
    theta0 = 0.5 * (lo + hi)
    z0 = np.clip((theta0 - lo) / span, 0.0, 1.0)
    lam0 = popsize if popsize > 0 else 4 + int(3 * np.log(d))
    history_writer.initialise()

    global_best_lp = -np.inf
    global_best_theta = theta0.copy()
    global_best_sim = None
    total_evals = 0
    t0 = time.time()
    rng = np.random.default_rng(seed)

    for restart in range(restarts):
        if total_evals >= max_evals:
            break
        restart_eval_limit = max_evals * (restart + 1) // restarts
        lam = lam0 * (2 ** restart)
        mu = lam // 2
        weights = np.log(mu + 0.5) - np.log(np.arange(1, mu + 1))
        weights /= np.sum(weights)
        mueff = 1.0 / np.sum(weights**2)

        cc = (4.0 + mueff / d) / (d + 4.0 + 2.0 * mueff / d)
        cs = (mueff + 2.0) / (d + mueff + 5.0)
        c1 = 2.0 / ((d + 1.3) ** 2 + mueff)
        cmu = min(1.0 - c1, 2.0 * (mueff - 2.0 + 1.0 / mueff) / ((d + 2.0) ** 2 + mueff))
        damps = 1.0 + 2.0 * max(0.0, math.sqrt((mueff - 1.0) / (d + 1.0)) - 1.0) + cs
        chi_n = math.sqrt(d) * (1.0 - 1.0 / (4.0 * d) + 1.0 / (21.0 * d * d))

        mean = z0.copy() if restart == 0 else rng.uniform(0.0, 1.0, d)
        sigma = min(0.5, sigma0 * (1.5 ** restart))
        C = np.eye(d)
        pc = np.zeros(d)
        ps = np.zeros(d)
        generation = 0

        while total_evals < restart_eval_limit and sigma > 1e-7:
            generation += 1
            eigvals, B = np.linalg.eigh((C + C.T) * 0.5)
            eigvals = np.maximum(eigvals, 1e-14)
            D = np.sqrt(eigvals)
            BD = B * D
            invsqrtC = (B * (1.0 / D)) @ B.T

            arz = rng.standard_normal((lam, d))
            ary = arz @ BD.T
            candidates = reflect_unit(mean + sigma * ary)

            records: list[tuple[float, np.ndarray, np.ndarray, ObjectiveEvaluation]] = []
            batch: list[tuple[int, int, np.ndarray, np.ndarray, str]] = []
            for j, z in enumerate(candidates):
                if total_evals + len(batch) >= restart_eval_limit:
                    break
                evaluation_index = total_evals + len(batch) + 1
                theta = lo + z * span
                label = f"cma_r{restart + 1}_g{generation}_c{j + 1}"
                batch.append((evaluation_index, j, z.copy(), theta.copy(), label))

            if workers > 1 and len(batch) > 1:
                with ThreadPoolExecutor(max_workers=min(workers, len(batch))) as executor:
                    evaluations = list(executor.map(lambda item: evaluate(item[3], item[4]), batch))
            else:
                evaluations = [evaluate(theta, label) for _, _, _, theta, label in batch]

            for (evaluation_index, j, z, theta, _label), evaluation in zip(batch, evaluations):
                total_evals = evaluation_index
                objective = evaluation.objective
                records.append((objective, z.copy(), theta.copy(), evaluation))
                history_writer.append_row(
                    evaluation_index=total_evals,
                    restart=restart + 1,
                    generation=generation,
                    candidate=j + 1,
                    objective=objective,
                    log_post=evaluation.log_post,
                    reject_reason=evaluation.reject_reason,
                    worst_var=evaluation.worst_var,
                    start_used=evaluation.start_used,
                    theta=theta.tolist(),
                    simulated_targets=evaluation.simulated_targets,
                )
                if math.isfinite(evaluation.log_post) and evaluation.log_post > global_best_lp:
                    global_best_lp = evaluation.log_post
                    global_best_theta = theta.copy()
                    global_best_sim = evaluation.simulated_targets
                    save_best(
                        best_path,
                        theta=global_best_theta.tolist(),
                        param_names=param_names,
                        log_post=global_best_lp,
                        objective=-global_best_lp,
                        method="cmaes",
                        simulated_targets=global_best_sim,
                        reject_reason=evaluation.reject_reason,
                        worst_var=evaluation.worst_var,
                        start_used=evaluation.start_used,
                        metadata=evaluation.metadata,
                    )

            if len(records) < mu:
                break
            records.sort(key=lambda item: item[0])
            if records[0][0] >= 1e99:
                sigma = min(0.5, sigma * 1.5)
                mean = rng.uniform(0.0, 1.0, d)
                continue

            old_mean = mean.copy()
            selected = np.array([item[1] for item in records[:mu]])
            mean = np.sum(weights[:, None] * selected, axis=0)
            y_w = (mean - old_mean) / sigma
            ps = (1.0 - cs) * ps + math.sqrt(cs * (2.0 - cs) * mueff) * (invsqrtC @ y_w)
            ps_norm = np.linalg.norm(ps)
            hsig_denom = math.sqrt(max(1.0e-16, 1.0 - (1.0 - cs) ** (2.0 * generation)))
            hsig = float(ps_norm / hsig_denom < (1.4 + 2.0 / (d + 1.0)) * chi_n)
            pc = (1.0 - cc) * pc + hsig * math.sqrt(cc * (2.0 - cc) * mueff) * y_w

            y_sel = (selected - old_mean) / sigma
            rank_mu = np.einsum("i,ij,ik->jk", weights, y_sel, y_sel)
            C = (1.0 - c1 - cmu) * C + c1 * (np.outer(pc, pc) + (1.0 - hsig) * cc * (2.0 - cc) * C) + cmu * rank_mu
            C = (C + C.T) * 0.5
            sigma *= math.exp((cs / damps) * (ps_norm / chi_n - 1.0))
            sigma = min(sigma, 1.0)

            elapsed = time.time() - t0
            gen_best_lp = records[0][3].log_post
            print(
                f"[eval {total_evals:6d}/{max_evals}]  restart={restart + 1}/{restarts}  gen={generation:4d}  "
                f"lp={gen_best_lp:9.3f}  best={global_best_lp:9.3f}  sigma={sigma:.4g}  t={elapsed:.0f}s"
            )

    return CMAESResult(
        best_theta=global_best_theta,
        best_log_post=global_best_lp,
        best_simulated_targets=global_best_sim,
        evaluations=total_evals,
    )
