using System;
using System.IO;
using System.Net;
using System.Text;
using System.Threading;

namespace SelectionProtocol
{
    public class HttpApi
    {
        private readonly HttpListener _listener;
        private readonly int _port;
        private Thread _listenerThread;
        private volatile bool _running;

        public HttpApi(int port)
        {
            _port = port;
            _listener = new HttpListener();
            _listener.Prefixes.Add($"http://localhost:{port}/");
        }

        public void Start()
        {
            if (_running) return;

            _running = true;
            _listener.Start();
            _listenerThread = new Thread(ListenLoop)
            {
                IsBackground = true,
                Name = "SelectionProtocol HTTP Listener"
            };
            _listenerThread.Start();

            Plugin.Logger.LogInfo($"HTTP API listening on port {_port}");
        }

        public void Stop()
        {
            if (!_running) return;

            _running = false;
            _listener.Stop();
            _listener.Close();

            Plugin.Logger.LogInfo("HTTP API stopped");
        }

        private void ListenLoop()
        {
            while (_running)
            {
                try
                {
                    var context = _listener.GetContext();
                    ThreadPool.QueueUserWorkItem(_ => HandleRequest(context));
                }
                catch (HttpListenerException)
                {
                    // Listener was stopped, exit gracefully
                    break;
                }
                catch (Exception ex)
                {
                    Plugin.Logger.LogError($"HTTP listener error: {ex.Message}");
                }
            }
        }

        private void HandleRequest(HttpListenerContext context)
        {
            try
            {
                var request = context.Request;
                var response = context.Response;

                Plugin.Logger.LogInfo($"{request.HttpMethod} {request.Url.PathAndQuery}");

                // Route handling
                if (request.HttpMethod == "GET" && request.Url.AbsolutePath == "/health")
                {
                    HandleHealth(response);
                }
                else
                {
                    Handle404(response);
                }
            }
            catch (Exception ex)
            {
                Plugin.Logger.LogError($"Request handling error: {ex.Message}");
            }
        }

        private void HandleHealth(HttpListenerResponse response)
        {
            var json = "{\"status\":\"ok\",\"plugin\":\"" + PluginInfo.PLUGIN_VERSION + "\"}";
            SendJsonResponse(response, json, 200);
        }

        private void Handle404(HttpListenerResponse response)
        {
            var json = "{\"error\":\"Not Found\"}";
            SendJsonResponse(response, json, 404);
        }

        private void SendJsonResponse(HttpListenerResponse response, string json, int statusCode)
        {
            response.StatusCode = statusCode;
            response.ContentType = "application/json";
            response.ContentEncoding = Encoding.UTF8;

            var bytes = Encoding.UTF8.GetBytes(json);
            response.ContentLength64 = bytes.Length;

            using (var output = response.OutputStream)
            {
                output.Write(bytes, 0, bytes.Length);
            }
        }
    }
}
