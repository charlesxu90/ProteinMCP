# Generate MSA file
pmcp install msa_mcp

Can you obtain the msa for TEV protease @examples/case3_fitness_modeling/TEVp.fasta using msa mcp and save it to @examples/case3_fitness_modeling/TEVp.a3m. 

# Build Plmc model based on the MSA
pmcp install plmc_mcp

I have created a a3m file for TEV protease in file @examples/case3_fitness_modeling/TEVp.a3m. Can you help build a ev model using plmc mcp and create it to @examples/case3_fitness_modeling/plmc directory. The wild-type sequence is @examples/case3_fitness_modeling/TEVp.fasta.

Please convert the relative path to absolution path before calling the MCP servers.

# Build EV+onehot model
pmcp install ev_onehot_mcp

I have created a plmc model for TEV protease  in directory @examples/case3_fitness_modeling/plmc. Can you help build a ev+onehot model using ev_onehot_mcp and create it to @examples/case3_fitness_modeling/ directory. The wild-type sequence is @examples/case3_fitness_modeling/TEVp.fasta, and the dataset is @examples/case3_fitness_modeling/data.csv.

Please convert the relative path to absolution path before calling the MCP servers.

# Build ESM models
pmcp install esm_mcp 

## ESM-650M
Can you help train a esm model for data @examples/case3_fitness_modeling/ and save it to 
@examples/case3_fitness_modeling/esm2_650M_{head_model} using the esm mcp server with svr, xgboost or knn as the head model.

Please convert the relative path to absolution path before calling the MCP servers. 
Obtain the embeddings if it is not created.

## ESM-3B
Can you help train a esm model for data @examples/case3_fitness_modeling/ and save it to 
@examples/case3_fitness_modeling/esm2_3B_{head_model} using the esm mcp server with svr, xgboost or knn as the head models and esm2_t36_3B_UR50D as the backbone.

Please convert the relative path to absolution path before calling the MCP servers. 
Obtain the embeddings if it is not created.


## ESM-1v models
Can you help train a esm model for data @examples/case3_fitness_modeling/ and save it to 
@examples/case3_fitness_modeling/esm1v_t33_650M_UR90S_{num}_{head_model} using the esm mcp server with svr, knn and xgboost as the head models and `esm1v_t33_650M_UR90S_1` to `esm1v_t33_650M_UR90S_5` as the backbone.

Please convert the relative path to absolution path before calling the MCP servers. 
Obtain the embeddings if it is not created.


# Build ProtTrans models
pmcp install prottrans_mcp
Can you help train a prottrans model for data @examples/case3_fitness_modeling/ and save it to 
@examples/case3_fitness_modeling/{backbone_model}_{head_model} using the prottrans mcp server with ProtT5-XL or ProtAlbert as backbone_model and knn, xgboost, and svr as the head model.

Please convert the relative path to absolution path before calling the MCP servers. 
Please create the embeddings if it is not created.

# Compare and plot the final figure
Now I have the metrics for ev+onehot and the different esm and ProtTrans models in @examples/case3*/metrics_summary.csv and @examples/case3*/*/training_summary.csv. Can you create a barchart figure with seaborn (show the mean and variances of spearman) to compares the backbone models? Please use the best head model obtained. 