#!/bin/bash

#for i in {1..1}; do 
#      ./run_servers.sh 3 python3 torch_runner.py --file=whirl_baselines/3m_torch with name=test3_3m_torch label=test3_3m_torch &
#done

for i in {1..2}; do 
      #./run_servers.sh ${i} python3 torch_runner.py --file=whirl_baselines/3m_torch_cnn with name=test3_3m_torch_cnn label=test3_3m_torch_cnn &
      #./run_servers.sh ${i} python3 torch_runner.py --file=whirl_baselines/2s3z_torch_cnn with name=test3_2s3z_torch_cnn label=test3_2s3z_torch_cnn &
      #./run_servers.sh ${i} python3 torch_runner.py --file=whirl_baselines/2s3z_torch with name=test3_2s3z_torch label=test3_2s3z_torch &
      #./run_servers.sh ${i} python3 torch_runner.py --file=whirl_baselines/5m_vs_6m_torch with name=test3_5m_vs_6m_torch label=test3_5m_vs_6m_torch &
      #./run_servers.sh ${i} python3 torch_runner.py --file=whirl_baselines/5m_vs_6m_torch_cnn with name=test3_5m_vs_6m_torch_cnn label=test3_5m_vs_6m_torch_cnn &
      #./run_servers.sh ${i} python3 torch_runner.py --file=whirl_baselines/corridor_torch with name=corridor_torch label=corridor_torch &
      #./run_servers.sh ${i} python3 tf14_runner.py --file=whirl_baselines/5m_vs_6m with name=5m_vs_6m_tf label=5m_vs_6m_tf &
      #./run_servers.sh ${i} python3 tf14_runner.py --file=whirl_baselines/3s_vs_5z with name=3s_vs_5z_tf label=3s_vs_5z_tf &
      # CUDA_VISIBLE_DEVICES=1,3 ./run_servers.sh ${i} python3 tf14_runner.py --file=whirl_baselines/vdn_MMM2 with name=vdn_MMM2_tf_v3 label=vdn_MMM2_tf_v3 &
      #./run_servers.sh ${i} python3 tf14_runner.py --file=whirl_baselines/corridor with name=corridor_tf label=corridor_tf &
      # ./run_servers.sh ${i} python3 tf14_runner.py --file=whirl_baselines/27m_vs_30m with name=27m_vs_30m_tf label=27m_vs_30m_tf &
      # ./run_servers.sh ${i} python3 tf14_runner.py --file=whirl_baselines/vdn_MMM2 with name=vdn_MMM2_tf label=vdn_MMM2_tf & 
      # ./run_servers.sh ${i} python3 tf14_runner.py --file=whirl_baselines/3s_vs_5z with name=3s_vs_5z_tf label=3s_vs_5z_tf &
      # ./run_servers_cpu.sh ${i} python3 tf14_runner.py --file=whirl_baselines/vdn_MMM2 with name=vdn_tf_MMM2_a label=vdn_rf_MMM2_a
      #./run_servers.sh ${i} python3 tf14_runner.py --file=whirl_baselines/vdn_3s5z_vs_ with name=vdn_tf_3s5z_vs_3s6z_a label=vdn_rf_3s5z_vs_3s6z_a	
      #./run_servers.sh ${i} python3 tf14_runner.py --file=whirl_baselines/vdn_MMM2 with name=vdn_tf_MMM2_a label=vdn_rf_MMM2_a
      #./run_servers.sh ${i} python3 tf14_runner.py --file=whirl_baselines/vdn_MMM2 with name=vdn_tf_MMM2_a label=vdn_rf_MMM2_a
      #./run_servers_cpu.sh ${i} python3 tf14_runner.py --file=whirl_baselines/2s3z with name=2s3z_tf_dash label=2s3z_tf_dash &
      # ./run_servers_cpu.sh ${i} python3 tf14_runner.py --file=whirl_baselines/bane_vs_bane with name=bane_tf_dash label=bane_tf_dash  &
      #./run_servers_cpu.sh ${i} python3 runner.py --file=smac/3s5z_vs_3s6z_torch_cv with name=3s5z_vs_3s6z_torch_cv_dash label=3s5z_vs_3s6z_torch_cv_dash  &
      #./run_servers_cpu.sh ${i} python3 tf14_runner.py --file=whirl_baselines/1c3s5z with name=1c3s5z_tf_dash label=1c3s5z_tf_dash  &
      # ./run_servers_cpu.sh ${i} python3 runner.py --file=smac/6h_vs_8z_torch_cv with name=6h_vs_8z_torch_cv_dash label=6h_vs_8z_torch_cv_dash  &
      # ./run_servers_cpu.sh ${i} python3 runner.py --tf --file=smac/2c_vs_64zg with name=2c_vs_64zg_tf_dash2 label=2c_vs_64zg_tf_dash2  &
      #./run_servers_cpu.sh ${i} python3 runner.py --file=smac/3s5z_vs_3s6z_torch with name=3s5z_vs_3s6z_torch_dash label=3s5z_vs_3s6z_torch_dash  &
      #./run_servers_cpu.sh ${i} python3 runner.py --file=smac/corridor_torch_cv with name=corridor_torch_cv_dash label=corridor_torch_cv_dash  &
      #./run_servers_cpu.sh ${i} python3 runner.py --file=smac/3s5z_vs_3s6z_torch_cv with name=3s5z_vs_3s6z_torch_cv_dash label=3s5z_vs_3s6z_torch_cv_dash  &
      #./run_servers_cpu.sh ${i} python3 tf14_runner.py --file=whirl_baselines/1c3s5z with name=1c3s5z_tf_dash label=1c3s5z_tf_dash  &
      #./run_servers_cpu.sh ${i} python3 runner.py --file=smac/3m_torch_cv_joint with name=3m_torch_cv_joint_dash label=3m_torch_cv_joint_dash  &
      #./run_servers_cpu.sh ${i} python3 runner.py --file=smac/3m_torch_cv with name=3m_torch_cv_dash label=3m_torch_cv_dash  &
      # ./run_servers_cpu.sh ${i} python3 runner.py --file=smac/3s5z_vs_3s6z_torch with name=3s5z_vs_3s6z_torch_dash label=3s5z_vs_3s6z_torch_dash  &
      # ./run_servers_cpu.sh ${i} python3 runner.py --file=smac/10m_vs_11m_torch with name=10m_vs_11m_torch_dash3 label=10m_vs_11m_torch_dash3  &
      ./run_servers_cpu.sh ${i} python3 runner.py --file=smac/10m_vs_11m_torch with name=10m_vs_11m_torch_dash3 label=10m_vs_11m_torch_dash3  &
      # ./run_servers_cpu.sh ${i} python3 runner.py --file=smac/3s5z_torch with name=3s5z_torch_dash3 label=3s5z_torch_dash3  &
done
