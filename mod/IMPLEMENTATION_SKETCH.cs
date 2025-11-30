/*
 * IMPLEMENTATION SKETCH - C# Mod API Extensions
 *
 * This file contains pseudocode/sketches for the new mod API endpoints.
 * NOT compiled code - reference for implementation.
 *
 * TODO before implementation:
 * 1. Decompile game code: ./decompile_dll.sh
 * 2. Find actual method names in mod/decompiled/
 * 3. Replace PLACEHOLDER comments with real Unity API calls
 *
 * Key files to search in decompiled code:
 * - ManagementScripts/UserControl.cs - Current target, selection
 * - SimulationScripts/BibiteScripts/*.cs - Bibite class, methods
 * - SimulationScripts/BibiteScripts/BibiteGenes.cs - Lineage tag field
 * - SimulationScripts/BibiteScripts/BibiteBody.cs - Energy, health
 * - ManagementScripts/TimeController.cs - Pause control (already done)
 * - ManagementScripts/CameraController.cs (?) - Zoom control
 * - UI/*.cs - Info panel visibility
 */

// ============================================================
// GameController.cs - New Methods
// ============================================================

namespace SelectionProtocol
{
    // Data structures
    public class TargetInfo
    {
        public int bibite_id;
        public string lineage_tag;
        public string species;
        public float age;
        public float energy;
        public bool can_kill;
        public bool can_lay;
    }

    public class ActionResult
    {
        public bool success;
        public string action;
        public string message;

        public static ActionResult Success(string action)
        {
            return new ActionResult { success = true, action = action };
        }

        public static ActionResult Failure(string action, string message)
        {
            return new ActionResult { success = false, action = action, message = message };
        }
    }

    public partial class GameController
    {
        // ============================================================
        // TARGET INFO RETRIEVAL
        // ============================================================

        public void GetTargetInfo(Action<TargetInfo> callback)
        {
            EnqueueCommand(() =>
            {
                // PLACEHOLDER: Find actual method to get current target
                // Search: grep -r "GetCurrentTarget\|SelectedBibite\|CurrentBibite" mod/decompiled/
                var target = UserControl.Instance.GetCurrentTarget();  // ???

                if (target == null)
                {
                    Plugin.Logger.LogInfo("GetTargetInfo: No target selected");
                    callback(null);
                    return;
                }

                // PLACEHOLDER: Find actual field/property names
                // Search: grep -r "class.*Bibite" mod/decompiled/ -A 50
                var info = new TargetInfo
                {
                    bibite_id = target.GetInstanceID(),
                    lineage_tag = target.genes.lineageTag,  // ???
                    species = target.genes.species,  // ???
                    age = target.age,  // ???
                    energy = target.body.energy,  // ???
                    can_kill = true,  // Always can kill
                    can_lay = CanBibiteReproduce(target)  // Helper method below
                };

                Plugin.Logger.LogInfo($"GetTargetInfo: ID={info.bibite_id}, tag={info.lineage_tag}, age={info.age}");
                callback(info);
            });
        }

        private bool CanBibiteReproduce(Bibite target)  // PLACEHOLDER: Actual Bibite class name
        {
            // PLACEHOLDER: Find actual reproduction validation logic
            // Search: grep -r "CanReproduce\|Reproduce\|LayEgg" mod/decompiled/
            // Likely checks:
            // - Age > minimum (e.g., 10 seconds)
            // - Energy > threshold (e.g., 50)
            // - Not currently pregnant
            // - Not recently reproduced (cooldown)

            // Example (replace with actual):
            if (target.age < 10.0f) return false;
            if (target.body.energy < 50.0f) return false;
            if (target.isPregnant) return false;  // ???
            return true;
        }

        // ============================================================
        // TARGET KILL ACTION
        // ============================================================

        public void KillTarget(Action<ActionResult> callback)
        {
            EnqueueCommand(() =>
            {
                // PLACEHOLDER: Find actual method to get current target
                var target = UserControl.Instance.GetCurrentTarget();

                if (target == null)
                {
                    Plugin.Logger.LogWarning("KillTarget: No target selected");
                    callback(ActionResult.Failure("kill", "No target selected"));
                    return;
                }

                // PLACEHOLDER: Find actual kill method
                // Search: grep -r "Kill()\|Death\|Die" mod/decompiled/
                // Likely options:
                // - target.Kill()
                // - target.Die()
                // - target.body.Kill()
                // - BibitesManager.Instance.KillBibite(target)

                try
                {
                    target.Kill();  // ???
                    Plugin.Logger.LogInfo($"KillTarget: Killed bibite {target.GetInstanceID()}");
                    callback(ActionResult.Success("kill"));
                }
                catch (Exception ex)
                {
                    Plugin.Logger.LogError($"KillTarget: Exception - {ex.Message}");
                    callback(ActionResult.Failure("kill", $"Exception: {ex.Message}"));
                }
            });
        }

        // ============================================================
        // TARGET LAY ACTION (with lineage tag)
        // ============================================================

        public void LayTarget(string lineageTag, Action<ActionResult> callback)
        {
            EnqueueCommand(() =>
            {
                // PLACEHOLDER: Find actual method to get current target
                var target = UserControl.Instance.GetCurrentTarget();

                // Validate target exists
                if (target == null)
                {
                    Plugin.Logger.LogWarning("LayTarget: No target selected");
                    callback(ActionResult.Failure("lay", "No target selected"));
                    return;
                }

                // Validate can reproduce
                if (!CanBibiteReproduce(target))
                {
                    Plugin.Logger.LogWarning($"LayTarget: Cannot reproduce (age={target.age}, energy={target.body.energy})");
                    callback(ActionResult.Failure("lay", "Target cannot reproduce (age/energy/state)"));
                    return;
                }

                try
                {
                    // Pause game (if not already paused)
                    bool wasPaused = TimeController.paused;
                    if (!wasPaused)
                    {
                        TimeController.Instance.TogglePauseGame("base");
                        Plugin.Logger.LogInfo("LayTarget: Paused game");
                    }

                    // PLACEHOLDER: Find actual lineage tag field
                    // Search: grep -r "lineageTag\|LineageTag\|parentTag" mod/decompiled/
                    // Set lineage tag (direct field access - no UI, no clipboard)
                    target.genes.lineageTag = lineageTag;  // ???
                    Plugin.Logger.LogInfo($"LayTarget: Set lineage tag to '{lineageTag}'");

                    // PLACEHOLDER: Find actual reproduction method
                    // Search: grep -r "Reproduce\|LayEgg\|SpawnOffspring" mod/decompiled/
                    // Execute reproduction
                    target.Reproduce();  // ???
                    Plugin.Logger.LogInfo("LayTarget: Reproduction executed");

                    // Unpause game (if we paused it)
                    if (!wasPaused)
                    {
                        TimeController.Instance.TogglePauseGame("base");
                        Plugin.Logger.LogInfo("LayTarget: Unpaused game");
                    }

                    callback(ActionResult.Success("lay"));
                }
                catch (Exception ex)
                {
                    Plugin.Logger.LogError($"LayTarget: Exception - {ex.Message}");
                    callback(ActionResult.Failure("lay", $"Exception: {ex.Message}"));
                }
            });
        }

        // ============================================================
        // WORLD ZOOM CONTROL
        // ============================================================

        public void Zoom(string direction, Action<ActionResult> callback)
        {
            EnqueueCommand(() =>
            {
                // PLACEHOLDER: Find actual zoom methods
                // Search: grep -r "Zoom\|zoom" mod/decompiled/ | grep -i "in\|out\|method"
                // Likely options:
                // - CameraController.Instance.ZoomIn() / ZoomOut()
                // - UserControl.Instance.HandleZoom(delta)
                // - Camera.main.orthographicSize += delta

                try
                {
                    if (direction == "in")
                    {
                        // PLACEHOLDER: Call actual zoom in method
                        CameraController.Instance.ZoomIn();  // ???
                        Plugin.Logger.LogInfo("Zoom: Zoomed in");
                    }
                    else if (direction == "out")
                    {
                        // PLACEHOLDER: Call actual zoom out method
                        CameraController.Instance.ZoomOut();  // ???
                        Plugin.Logger.LogInfo("Zoom: Zoomed out");
                    }
                    else
                    {
                        Plugin.Logger.LogWarning($"Zoom: Invalid direction '{direction}'");
                        callback(ActionResult.Failure("zoom", $"Invalid direction: {direction}"));
                        return;
                    }

                    callback(ActionResult.Success("zoom"));
                }
                catch (Exception ex)
                {
                    Plugin.Logger.LogError($"Zoom: Exception - {ex.Message}");
                    callback(ActionResult.Failure("zoom", $"Exception: {ex.Message}"));
                }
            });
        }

        // ============================================================
        // WORLD INFO PANEL CONTROL
        // ============================================================

        public void SetInfoPanel(int panel, Action<ActionResult> callback)
        {
            EnqueueCommand(() =>
            {
                // PLACEHOLDER: Find actual info panel methods
                // Search: grep -r "InfoPanel\|Panel\|UI.*Visibility\|ShowPanel\|HidePanel" mod/decompiled/
                // Likely options:
                // - UIController.Instance.SetActivePanel(panel)
                // - UserControl.Instance.HandleInfoPanelKey(panel)
                // - PanelManager.Instance.ShowPanel(panel) / HideAll()

                try
                {
                    if (panel < 0 || panel > 4)
                    {
                        Plugin.Logger.LogWarning($"SetInfoPanel: Invalid panel {panel}");
                        callback(ActionResult.Failure("info_panel", $"Invalid panel: {panel}"));
                        return;
                    }

                    if (panel == 0)
                    {
                        // PLACEHOLDER: Hide all panels
                        UIController.Instance.HideAllPanels();  // ???
                        Plugin.Logger.LogInfo("SetInfoPanel: Hid all panels");
                    }
                    else
                    {
                        // PLACEHOLDER: Show specific panel
                        UIController.Instance.SetActivePanel(panel);  // ???
                        Plugin.Logger.LogInfo($"SetInfoPanel: Showing panel {panel}");
                    }

                    callback(ActionResult.Success("info_panel"));
                }
                catch (Exception ex)
                {
                    Plugin.Logger.LogError($"SetInfoPanel: Exception - {ex.Message}");
                    callback(ActionResult.Failure("info_panel", $"Exception: {ex.Message}"));
                }
            });
        }
    }
}

// ============================================================
// ApiHandlers.cs - New Endpoint Handlers
// ============================================================

namespace SelectionProtocol
{
    public partial class ApiHandlers
    {
        // ============================================================
        // /target/info - Get current target info
        // ============================================================

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
                        $"\"lineage_tag\":\"{targetInfo.lineage_tag}\"," +
                        $"\"species\":\"{targetInfo.species}\"," +
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

        // ============================================================
        // /target/kill - Kill current target
        // ============================================================

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
                    json += $",\"message\":\"{result.message}\"";
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

        // ============================================================
        // /target/lay - Lay target with lineage tag
        // ============================================================

        public void HandleLayTarget(HttpListenerRequest request, HttpListenerResponse response)
        {
            // Parse request body to get lineage_tag
            string lineageTag = null;
            try
            {
                using (var reader = new System.IO.StreamReader(request.InputStream, request.ContentEncoding))
                {
                    var body = reader.ReadToEnd();
                    // Simple JSON parsing (TODO: use proper library if needed)
                    // Expected: {"lineage_tag": "username"}
                    var match = System.Text.RegularExpressions.Regex.Match(body, @"""lineage_tag""\s*:\s*""([^""]+)""");
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
                    json += $",\"message\":\"{result.message}\"";
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

        // ============================================================
        // /world/zoom - Zoom in/out
        // ============================================================

        public void HandleZoom(HttpListenerRequest request, HttpListenerResponse response)
        {
            // Parse request body to get direction
            string direction = null;
            try
            {
                using (var reader = new System.IO.StreamReader(request.InputStream, request.ContentEncoding))
                {
                    var body = reader.ReadToEnd();
                    // Expected: {"direction": "in"} or {"direction": "out"}
                    var match = System.Text.RegularExpressions.Regex.Match(body, @"""direction""\s*:\s*""([^""]+)""");
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
                    json += $",\"message\":\"{result.message}\"";
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

        // ============================================================
        // /world/info_panel - Set info panel visibility
        // ============================================================

        public void HandleInfoPanel(HttpListenerRequest request, HttpListenerResponse response)
        {
            // Parse request body to get panel number
            int panel = -1;
            try
            {
                using (var reader = new System.IO.StreamReader(request.InputStream, request.ContentEncoding))
                {
                    var body = reader.ReadToEnd();
                    // Expected: {"panel": 0-4}
                    var match = System.Text.RegularExpressions.Regex.Match(body, @"""panel""\s*:\s*(\d+)");
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
                    json += $",\"message\":\"{result.message}\"";
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
    }
}

// ============================================================
// HttpApi.cs - New Routes (add to HandleRequest)
// ============================================================

/*
Add these to the if/else chain in HttpApi.cs HandleRequest() method:

else if (request.HttpMethod == "POST" && request.Url.AbsolutePath == "/target/info")
{
    _handlers.HandleGetTargetInfo(response);
}
else if (request.HttpMethod == "POST" && request.Url.AbsolutePath == "/target/kill")
{
    _handlers.HandleKillTarget(response);
}
else if (request.HttpMethod == "POST" && request.Url.AbsolutePath == "/target/lay")
{
    _handlers.HandleLayTarget(request, response);
}
else if (request.HttpMethod == "POST" && request.Url.AbsolutePath == "/world/zoom")
{
    _handlers.HandleZoom(request, response);
}
else if (request.HttpMethod == "POST" && request.Url.AbsolutePath == "/world/info_panel")
{
    _handlers.HandleInfoPanel(request, response);
}
*/

// ============================================================
// TESTING COMMANDS (curl examples)
// ============================================================

/*
# Health check
curl http://localhost:5001/health

# Get target info
curl -X POST http://localhost:5001/target/info

# Kill target
curl -X POST http://localhost:5001/target/kill

# Lay target with tag
curl -X POST http://localhost:5001/target/lay \
  -H "Content-Type: application/json" \
  -d '{"lineage_tag": "TestUser123"}'

# Zoom in
curl -X POST http://localhost:5001/world/zoom \
  -H "Content-Type: application/json" \
  -d '{"direction": "in"}'

# Zoom out
curl -X POST http://localhost:5001/world/zoom \
  -H "Content-Type: application/json" \
  -d '{"direction": "out"}'

# Show info panel 1
curl -X POST http://localhost:5001/world/info_panel \
  -H "Content-Type: application/json" \
  -d '{"panel": 1}'

# Hide all panels
curl -X POST http://localhost:5001/world/info_panel \
  -H "Content-Type: application/json" \
  -d '{"panel": 0}'
*/
