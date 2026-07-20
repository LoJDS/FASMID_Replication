cd FASMID
#BSUB -J CMAES_FASMID
#BSUB -oo /work/cmcc/ld13424/FASMID/FASMID_Logs/CMAES_FASMID.out
#BSUB -eo /work/cmcc/ld13424/FASMID/FASMID_Logs/CMAES_FASMID.err
#BSUB -n 36
#BSUB -q p_long
#BSUB -x 
#BSUB -P 0588

#module load gcc_9.1.0/9.1.0
module purge
module load glib/2.74.1-2mxe7
source /work/cmcc/ld13424/miniconda3/initialize_miniconda.sh
conda activate test_gpu

 
python3 -m CMAESCalibrator run --config cmaes_config.example.yaml > CMAES_FASMID.txt

