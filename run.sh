python -m lightllm.server.api_server --model_dir ../hf-codellama-34b-instruct --host 0.0.0.0 --port 9090 --tp 4 --max_total_token_num 120000 --long_truncation_mode center
