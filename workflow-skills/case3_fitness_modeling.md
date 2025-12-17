# Generate MSA file 
Can you obtain the msa for TEV protease @examples/case3_fitness_modeling/TEVp.fasta using msa mcp and save it to @examples/case3_fitness_modeling/TEVp.a3m. 

# Build WebLogo for the input sequence
I have created a a3m file for TEV protease in file @examples/case3_fitness_modeling/TEVp.a3m. Can you help build a ev model using plmc mcp and create it to @examples/case3_fitness_modeling/plmc directory. The wild-type sequence is @examples/case3_fitness_modeling/TEVp.fasta.

Please convert the relative path to absolution path before calling the MCP servers.

# Build EV+onehot model
I have created a plmc model for TEV protease  in directory @examples/case3_fitness_modeling/plmc. Can you help build a ev+onehot model using ev_onehot_mcp and create it to @examples/case3_fitness_modeling/ directory. The wild-type sequence is @examples/case3_fitness_modeling/TEVp.fasta, and the dataset is @examples/case3_fitness_modeling/data.csv.

Please convert the relative path to absolution path before calling the MCP servers.

# Build ESM models

Can you help train a esm model for data @examples/case3_fitness_modeling/ and save it to 
@examples/case3_fitness_modeling/esm2_650M_knn using the esm mcp server with knn as the head model.

Please convert the relative path to absolution path before calling the MCP servers. 

# Build ProtTrans models
Can you help train a prottrans model for data @examples/case3_fitness_modeling/ and save it to 
@examples/case3_fitness_modeling/prott5_knn using the prottrans mcp server with ProtT5-XL for embedding and knn as the head model.

Please convert the relative path to absolution path before calling the MCP servers. 
