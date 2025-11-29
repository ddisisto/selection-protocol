using System;
using System.Net;
using System.Threading;

namespace SelectionProtocol
{
    /// <summary>
    /// HTTP infrastructure layer. Manages listener lifecycle and routes requests to handlers.
    /// </summary>
    public class HttpApi
    {
        private readonly HttpListener _listener;
        private readonly int _port;
        private readonly ApiHandlers _handlers;
        private Thread _listenerThread;
        private volatile bool _running;

        public HttpApi(int port, ApiHandlers handlers)
        {
            _port = port;
            _handlers = handlers;
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

                // Route to appropriate handler
                if (request.HttpMethod == "GET" && request.Url.AbsolutePath == "/health")
                {
                    _handlers.HandleHealth(response);
                }
                else
                {
                    _handlers.Handle404(response);
                }
            }
            catch (Exception ex)
            {
                Plugin.Logger.LogError($"Request handling error: {ex.Message}");
            }
        }
    }
}
