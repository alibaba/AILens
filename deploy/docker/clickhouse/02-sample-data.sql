-- Sample OTLP trace data for quick start
-- A simple web application trace: frontend → api-gateway → user-service → database

-- Trace 1: Successful user login flow
INSERT INTO default.otel_traces VALUES
(now64(9), 'aaaa1111bbbb2222cccc3333dddd4444', '1000000000000001', '', 'POST /api/login', 'SERVER', 'api-gateway', 850000000, 'OK', '', map('service.name','api-gateway','host.name','gateway-pod-1'), map('http.method','POST','http.url','/api/login','http.status_code','200'), [], [], [], [], []),
(now64(9), 'aaaa1111bbbb2222cccc3333dddd4444', '1000000000000002', '1000000000000001', 'getUserByName', 'CLIENT', 'api-gateway', 600000000, 'OK', '', map('service.name','api-gateway'), map('rpc.service','UserService','rpc.method','getUserByName'), [], [], [], [], []),
(now64(9), 'aaaa1111bbbb2222cccc3333dddd4444', '1000000000000003', '1000000000000002', 'getUserByName', 'SERVER', 'user-service', 550000000, 'OK', '', map('service.name','user-service','host.name','user-pod-1'), map('rpc.service','UserService','rpc.method','getUserByName'), [], [], [], [], []),
(now64(9), 'aaaa1111bbbb2222cccc3333dddd4444', '1000000000000004', '1000000000000003', 'SELECT users', 'CLIENT', 'user-service', 120000000, 'OK', '', map('service.name','user-service'), map('db.system','mysql','db.statement','SELECT * FROM users WHERE name = ?'), [], [], [], [], []);

-- Trace 2: Failed order creation
INSERT INTO default.otel_traces VALUES
(now64(9), 'eeee5555ffff6666aaaa7777bbbb8888', '2000000000000001', '', 'POST /api/orders', 'SERVER', 'api-gateway', 1200000000, 'ERROR', 'Internal Server Error', map('service.name','api-gateway'), map('http.method','POST','http.url','/api/orders','http.status_code','500'), [], [], [], [], []),
(now64(9), 'eeee5555ffff6666aaaa7777bbbb8888', '2000000000000002', '2000000000000001', 'createOrder', 'CLIENT', 'api-gateway', 1000000000, 'ERROR', 'timeout', map('service.name','api-gateway'), map('rpc.service','OrderService','rpc.method','createOrder'), [], [], [], [], []),
(now64(9), 'eeee5555ffff6666aaaa7777bbbb8888', '2000000000000003', '2000000000000002', 'createOrder', 'SERVER', 'order-service', 950000000, 'ERROR', 'database timeout', map('service.name','order-service'), map('rpc.service','OrderService','rpc.method','createOrder'), [], [], [], [], []),
(now64(9), 'eeee5555ffff6666aaaa7777bbbb8888', '2000000000000004', '2000000000000003', 'INSERT orders', 'CLIENT', 'order-service', 900000000, 'ERROR', 'connection timeout', map('service.name','order-service'), map('db.system','mysql','db.statement','INSERT INTO orders ...'), [], [], [], [], []);

-- Trace 3: AI agent conversation
INSERT INTO default.otel_traces VALUES
(now64(9), 'cccc9999dddd0000eeee1111ffff2222', '3000000000000001', '', 'invoke_agent coding_assistant', 'SERVER', 'agent-server', 5000000000, 'OK', '', map('service.name','agent-server'), map('gen_ai.span_kind_name','AGENT','gen_ai.conversation.id','session-001'), [], [], [], [], []),
(now64(9), 'cccc9999dddd0000eeee1111ffff2222', '3000000000000002', '3000000000000001', 'chat qwen-72b', 'CLIENT', 'agent-server', 3200000000, 'OK', '', map('service.name','agent-server'), map('gen_ai.span_kind_name','LLM','gen_ai.operation.name','chat','gen_ai.request.model','qwen-72b','gen_ai.usage.input_tokens','512','gen_ai.usage.output_tokens','128'), [], [], [], [], []),
(now64(9), 'cccc9999dddd0000eeee1111ffff2222', '3000000000000003', '3000000000000001', 'execute_tool write_file', 'CLIENT', 'agent-server', 500000000, 'OK', '', map('service.name','agent-server'), map('gen_ai.span_kind_name','TOOL','tool.name','write_file'), [], [], [], [], []),
(now64(9), 'cccc9999dddd0000eeee1111ffff2222', '3000000000000004', '3000000000000001', 'chat qwen-72b', 'CLIENT', 'agent-server', 2100000000, 'OK', '', map('service.name','agent-server'), map('gen_ai.span_kind_name','LLM','gen_ai.operation.name','chat','gen_ai.request.model','qwen-72b','gen_ai.usage.input_tokens','768','gen_ai.usage.output_tokens','256'), [], [], [], [], []);
