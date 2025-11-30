using System;
using System.Net;
using System.Text;
using System.Threading;

namespace SelectionProtocol
{
    /// <summary>
    /// HTTP endpoint handlers. Calls GameController methods and returns JSON responses.
    /// </summary>
    public class ApiHandlers
    {
        private readonly GameController _gameController;

        public ApiHandlers(GameController gameController)
        {
            _gameController = gameController;
            Plugin.Logger.LogInfo("ApiHandlers initialized");
        }

        public void HandleHealth(HttpListenerResponse response)
        {
            var json = "{\"status\":\"ok\",\"plugin\":\"" + PluginInfo.PLUGIN_VERSION + "\"}";
            SendJsonResponse(response, json, 200);
        }

        public void HandleGetPause(HttpListenerResponse response)
        {
            if (!_gameController.IsGameReady())
            {
                var errorJson = "{\"error\":\"Game not ready\"}";
                SendJsonResponse(response, errorJson, 503);
                return;
            }

            // Use ManualResetEvent to wait for callback from main thread
            var resetEvent = new ManualResetEvent(false);
            bool pauseState = false;

            _gameController.GetPauseState(state =>
            {
                pauseState = state;
                resetEvent.Set();
            });

            // Wait for main thread to execute command (timeout 5s)
            if (resetEvent.WaitOne(5000))
            {
                var json = "{\"paused\":" + (pauseState ? "true" : "false") + "}";
                SendJsonResponse(response, json, 200);
            }
            else
            {
                var errorJson = "{\"error\":\"Timeout waiting for game state\"}";
                SendJsonResponse(response, errorJson, 504);
            }
        }

        public void HandlePostPause(HttpListenerResponse response)
        {
            if (!_gameController.IsGameReady())
            {
                var errorJson = "{\"error\":\"Game not ready\"}";
                SendJsonResponse(response, errorJson, 503);
                return;
            }

            // Use ManualResetEvent to wait for callback from main thread
            var resetEvent = new ManualResetEvent(false);
            bool newPauseState = false;

            _gameController.TogglePause(state =>
            {
                newPauseState = state;
                resetEvent.Set();
            });

            // Wait for main thread to execute command (timeout 5s)
            if (resetEvent.WaitOne(5000))
            {
                var json = "{\"paused\":" + (newPauseState ? "true" : "false") + "}";
                SendJsonResponse(response, json, 200);
            }
            else
            {
                var errorJson = "{\"error\":\"Timeout waiting for pause toggle\"}";
                SendJsonResponse(response, errorJson, 504);
            }
        }

        public void Handle404(HttpListenerResponse response)
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
