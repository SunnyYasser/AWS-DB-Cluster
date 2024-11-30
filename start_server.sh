source lab3/bin/activate
pip install -r requirements.txt
cd infra
python3 main.py
cd ../client
python3 benchmark.py
