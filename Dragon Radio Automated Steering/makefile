.PHONY: run_tran run_recv send run install

run_tran: automated_steering.py
	dragonradio ~/lab6/sdr-class-radio.py -f 3.502e9 -i 2 --arq --interactive

run_recv: automated_steering.py
	dragonradio ~/lab6/sdr-class-radio.py -f 3.502e9 -i 1 --arq --interactive

send: automated_steering.py
	scp automated_steering.py dwsl:~/autonomous_steering/
	scp makefile dwsl:~/autonomous_steering/
	scp ML_models/* dwsl:~/autonomous_steering/ML_models/

install:
	pip3 install joblib
	pip3 install scikit-learn==1.0.1