set -e
cd blockchain

cd PublicKeysReadersContract
echo "Deploying PKReadersContract"
python3.10 PKReadersContractMainCreation.py
#python3.10 blockchain/PublicKeysReadersContract/PKReadersContractMain.py -d
echo "Deployed PKReadersContract"

cd ../AttributeCertifierContract
echo "Deploying AttributeCertifierContract"
python3.10 AttributeCertifierContractMainCreation.py
#python3.10 blockchain/AttributeCertifierContract/AttributeCertifierContractMain.py -d
echo "Deployed AttributeCertifierContract \n"

cd ../MessageContract
echo "Deploying MessageContract"
python3.10 MessageContractMainCreation.py 
#python3.10 blockchain/MessageContract/MessageContractMain.py -d
echo "Deployed MessageContract \n"

cd ../BoxContract
echo "Deploying BoxContract"
python3.10 BoxContract.py
python3.10 BoxContractMainCreation.py -f
#python3.10 blockchain/PublicKeySKM/BoxContractMainCreation.py -d
echo "Deployed BoxContract \n"