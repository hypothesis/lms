/** The entry point for the postmessage_json_rpc_server bundle. */
"use strict";

import Server from "./server"
import { requestConfig } from "./methods"

const serverConfig = JSON.parse(document.getElementsByClassName("js-rpc-server-config")[0].textContent);
const server = new Server(serverConfig);
server.register("requestConfig", requestConfig);
