using System;
using System.IO;
using System.Net;
using System.Text;
using System.Text.RegularExpressions;
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

        public void HandleGetTargetInfo(HttpListenerResponse response)
        {
            var resetEvent = new ManualResetEvent(false);
            TargetInfo targetInfo = null;

            _gameController.GetTargetInfo(info =>
            {
                targetInfo = info;
                resetEvent.Set();
            });

            if (resetEvent.WaitOne(5000))
            {
                if (targetInfo == null)
                {
                    // No target selected - return null (valid state)
                    SendJsonResponse(response, "null", 200);
                }
                else
                {
                    // Serialize target info to JSON
                    var json = "{" +
                        $"\"bibite_id\":{targetInfo.bibite_id}," +
                        $"\"lineage_tag\":\"{EscapeJson(targetInfo.lineage_tag)}\"," +
                        $"\"age\":{targetInfo.age}," +
                        $"\"energy\":{targetInfo.energy}," +
                        $"\"can_kill\":{(targetInfo.can_kill ? "true" : "false")}," +
                        $"\"can_lay\":{(targetInfo.can_lay ? "true" : "false")}" +
                        "}";
                    SendJsonResponse(response, json, 200);
                }
            }
            else
            {
                var errorJson = "{\"error\":\"Timeout waiting for target info\"}";
                SendJsonResponse(response, errorJson, 504);
            }
        }

        public void HandleKillTarget(HttpListenerResponse response)
        {
            var resetEvent = new ManualResetEvent(false);
            ActionResult result = null;

            _gameController.KillTarget(r =>
            {
                result = r;
                resetEvent.Set();
            });

            if (resetEvent.WaitOne(5000))
            {
                var json = "{" +
                    $"\"success\":{(result.success ? "true" : "false")}," +
                    $"\"action\":\"{result.action}\"";
                if (result.message != null)
                {
                    json += $",\"message\":\"{EscapeJson(result.message)}\"";
                }
                json += "}";

                SendJsonResponse(response, json, 200);
            }
            else
            {
                var errorJson = "{\"error\":\"Timeout waiting for kill action\"}";
                SendJsonResponse(response, errorJson, 504);
            }
        }

        public void HandleLayTarget(HttpListenerRequest request, HttpListenerResponse response)
        {
            // Parse request body to get lineage_tag
            string lineageTag = null;
            try
            {
                using (var reader = new StreamReader(request.InputStream, request.ContentEncoding))
                {
                    var body = reader.ReadToEnd();
                    // Simple JSON parsing: {"lineage_tag": "username"}
                    var match = Regex.Match(body, @"""lineage_tag""\s*:\s*""([^""]+)""");
                    if (match.Success)
                    {
                        lineageTag = match.Groups[1].Value;
                    }
                }
            }
            catch (Exception ex)
            {
                Plugin.Logger.LogError($"HandleLayTarget: Failed to parse request body - {ex.Message}");
                var errorJson = "{\"error\":\"Invalid request body\"}";
                SendJsonResponse(response, errorJson, 400);
                return;
            }

            if (string.IsNullOrEmpty(lineageTag))
            {
                var errorJson = "{\"error\":\"Missing lineage_tag in request body\"}";
                SendJsonResponse(response, errorJson, 400);
                return;
            }

            // Execute lay action
            var resetEvent = new ManualResetEvent(false);
            ActionResult result = null;

            _gameController.LayTarget(lineageTag, r =>
            {
                result = r;
                resetEvent.Set();
            });

            if (resetEvent.WaitOne(5000))
            {
                var json = "{" +
                    $"\"success\":{(result.success ? "true" : "false")}," +
                    $"\"action\":\"{result.action}\"";
                if (result.message != null)
                {
                    json += $",\"message\":\"{EscapeJson(result.message)}\"";
                }
                json += "}";

                SendJsonResponse(response, json, 200);
            }
            else
            {
                var errorJson = "{\"error\":\"Timeout waiting for lay action\"}";
                SendJsonResponse(response, errorJson, 504);
            }
        }

        public void HandleZoom(HttpListenerRequest request, HttpListenerResponse response)
        {
            // Parse request body to get direction
            string direction = null;
            try
            {
                using (var reader = new StreamReader(request.InputStream, request.ContentEncoding))
                {
                    var body = reader.ReadToEnd();
                    // Expected: {"direction": "in"} or {"direction": "out"}
                    var match = Regex.Match(body, @"""direction""\s*:\s*""([^""]+)""");
                    if (match.Success)
                    {
                        direction = match.Groups[1].Value;
                    }
                }
            }
            catch (Exception ex)
            {
                Plugin.Logger.LogError($"HandleZoom: Failed to parse request body - {ex.Message}");
                var errorJson = "{\"error\":\"Invalid request body\"}";
                SendJsonResponse(response, errorJson, 400);
                return;
            }

            if (direction != "in" && direction != "out")
            {
                var errorJson = "{\"error\":\"Invalid direction (must be 'in' or 'out')\"}";
                SendJsonResponse(response, errorJson, 400);
                return;
            }

            // Execute zoom
            var resetEvent = new ManualResetEvent(false);
            ActionResult result = null;

            _gameController.Zoom(direction, r =>
            {
                result = r;
                resetEvent.Set();
            });

            if (resetEvent.WaitOne(5000))
            {
                var json = "{" +
                    $"\"success\":{(result.success ? "true" : "false")}," +
                    $"\"action\":\"{result.action}\"";
                if (result.message != null)
                {
                    json += $",\"message\":\"{EscapeJson(result.message)}\"";
                }
                json += "}";

                SendJsonResponse(response, json, 200);
            }
            else
            {
                var errorJson = "{\"error\":\"Timeout waiting for zoom\"}";
                SendJsonResponse(response, errorJson, 504);
            }
        }

        public void HandleInfoPanel(HttpListenerRequest request, HttpListenerResponse response)
        {
            // Parse request body to get panel number
            int panel = -1;
            try
            {
                using (var reader = new StreamReader(request.InputStream, request.ContentEncoding))
                {
                    var body = reader.ReadToEnd();
                    // Expected: {"panel": 0-4}
                    var match = Regex.Match(body, @"""panel""\s*:\s*(\d+)");
                    if (match.Success)
                    {
                        panel = int.Parse(match.Groups[1].Value);
                    }
                }
            }
            catch (Exception ex)
            {
                Plugin.Logger.LogError($"HandleInfoPanel: Failed to parse request body - {ex.Message}");
                var errorJson = "{\"error\":\"Invalid request body\"}";
                SendJsonResponse(response, errorJson, 400);
                return;
            }

            if (panel < 0 || panel > 4)
            {
                var errorJson = "{\"error\":\"Invalid panel (must be 0-4)\"}";
                SendJsonResponse(response, errorJson, 400);
                return;
            }

            // Execute info panel change
            var resetEvent = new ManualResetEvent(false);
            ActionResult result = null;

            _gameController.SetInfoPanel(panel, r =>
            {
                result = r;
                resetEvent.Set();
            });

            if (resetEvent.WaitOne(5000))
            {
                var json = "{" +
                    $"\"success\":{(result.success ? "true" : "false")}," +
                    $"\"action\":\"{result.action}\"";
                if (result.message != null)
                {
                    json += $",\"message\":\"{EscapeJson(result.message)}\"";
                }
                json += "}";

                SendJsonResponse(response, json, 200);
            }
            else
            {
                var errorJson = "{\"error\":\"Timeout waiting for info panel change\"}";
                SendJsonResponse(response, errorJson, 504);
            }
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

        private string EscapeJson(string str)
        {
            if (string.IsNullOrEmpty(str)) return str;
            return str.Replace("\\", "\\\\").Replace("\"", "\\\"").Replace("\n", "\\n").Replace("\r", "\\r");
        }
    }
}
