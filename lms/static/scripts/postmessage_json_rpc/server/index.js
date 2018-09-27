/** The entry point for the postmessage_json_rpc_server bundle. */
import Server from './server';
import { requestConfig } from './methods';

const server = new Server();
server.register('requestConfig', requestConfig);
