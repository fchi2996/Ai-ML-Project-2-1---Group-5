To connect the csv writter :

1. move the csv-plugin folder to the main ml-agents folder
2. run this comand With connda in the ml-agents folder
   `conda activate mlagents`
   `pip install -e ./csv_plugin`

3. later run the trining ex.->
   `mlagents-learn config/ppo/3DBall.yaml --run-id=test_csv`

4. the csv file from the run should be in folder ->
   `results/csv_output/`
