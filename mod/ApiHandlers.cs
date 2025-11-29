using System;
using System.Net;
using System.Text;

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
