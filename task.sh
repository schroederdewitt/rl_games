./run.sh 0 python3 runner.py -tf --file=whirl_baselines/2s3z_cv &
./run.sh 1 python3 runner.py -tf --file=whirl_baselines/3s5z_vs_3s6z_cv &
./run.sh 2 python3 runner.py -tf --file=whirl_baselines/6h_vs_8z_cv &
./run.sh 3 python3 runner.py -tf --file=whirl_baselines/bane_vs_bane_cv &
./run.sh 4 python3 runner.py -tf --file=whirl_baselines/corridor_cv &
./run.sh 4 python3 runner.py -tf --file=whirl_baselines/corridor_cv & # two corridor
./run.sh 5 python3 runner.py -tf --file=whirl_baselines/MMM2_cv &
