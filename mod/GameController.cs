using System;
using ManagementScripts;
using SimulationScripts.BibiteScripts;
using UIScripts;
using UIScripts.UIPanels;
using UnityEngine;

namespace SelectionProtocol
{
    /// <summary>
    /// Data structure for target information response.
    /// </summary>
    public class TargetInfo
    {
        public int bibite_id;
        public string lineage_tag;
        public float age;
        public float energy;
        public bool can_kill;
        public bool can_lay;
    }

    /// <summary>
    /// Data structure for action result response.
    /// </summary>
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

    /// <summary>
    /// Bridges between HTTP API (background thread) and Unity game state (main thread).
    /// Handles command queueing and game state access.
    /// </summary>
    public class GameController
    {
        private readonly Action<Action> _enqueueCommand;

        public GameController(Action<Action> enqueueCommand)
        {
            _enqueueCommand = enqueueCommand;
            Plugin.Logger.LogInfo("GameController initialized");
        }

        /// <summary>
        /// Check if game is ready for state access (TimeController singleton initialized).
        /// </summary>
        public bool IsGameReady()
        {
            return TimeController.Instance != null;
        }

        /// <summary>
        /// Get current pause state.
        /// </summary>
        /// <param name="callback">Called with pause state on main thread</param>
        public void GetPauseState(Action<bool> callback)
        {
            EnqueueCommand(() =>
            {
                if (!IsGameReady())
                {
                    Plugin.Logger.LogWarning("GetPauseState: Game not ready");
                    callback(false);
                    return;
                }

                bool isPaused = TimeController.paused;
                Plugin.Logger.LogInfo($"GetPauseState: {isPaused}");
                callback(isPaused);
            });
        }

        /// <summary>
        /// Toggle pause state.
        /// </summary>
        /// <param name="callback">Called with new pause state on main thread</param>
        public void TogglePause(Action<bool> callback)
        {
            EnqueueCommand(() =>
            {
                if (!IsGameReady())
                {
                    Plugin.Logger.LogError("TogglePause: Game not ready");
                    callback(false);
                    return;
                }

                // Use "base" source to match spacebar behavior (avoid conflicting pause sources)
                TimeController.Instance.TogglePauseGame("base");
                bool newState = TimeController.paused;
                Plugin.Logger.LogInfo($"TogglePause: {newState}");
                callback(newState);
            });
        }

        /// <summary>
        /// Queue a command to execute on Unity main thread.
        /// </summary>
        private void EnqueueCommand(Action command)
        {
            _enqueueCommand(command);
        }

        /// <summary>
        /// Get information about the current target.
        /// </summary>
        /// <param name="callback">Called with target info on main thread (null if no target)</param>
        public void GetTargetInfo(Action<TargetInfo> callback)
        {
            EnqueueCommand(() =>
            {
                // Get current target from UserControl
                GameObject target = UserControl.Instance.target;

                if (target == null)
                {
                    Plugin.Logger.LogInfo("GetTargetInfo: No target selected");
                    callback(null);
                    return;
                }

                // Convert GameObject to BibiteBody
                BibiteBody body = target.GetComponent<BibiteBody>();
                if (body == null)
                {
                    Plugin.Logger.LogWarning("GetTargetInfo: Target is not a Bibite");
                    callback(null);
                    return;
                }

                // Build target info
                var info = new TargetInfo
                {
                    bibite_id = target.GetInstanceID(),
                    lineage_tag = body.gene.speciesTag ?? "",
                    age = body.age,
                    energy = body.Energy.Amount,
                    can_kill = !body.dead,
                    can_lay = CanBibiteReproduce(body)
                };

                Plugin.Logger.LogInfo($"GetTargetInfo: ID={info.bibite_id}, tag={info.lineage_tag}, age={info.age:F1}h, energy={info.energy:F1}");
                callback(info);
            });
        }

        /// <summary>
        /// Check if a bibite can reproduce (age, energy, maturity checks).
        /// </summary>
        private bool CanBibiteReproduce(BibiteBody body)
        {
            if (body.dead) return false;
            if (body.eggLayer == null) return false;
            if (!body.eggLayer.isMature) return false;

            // Additional validation could be added here if needed
            return true;
        }

        /// <summary>
        /// Kill the current target.
        /// Uses game's BibiteStatsPanel.KillCurrentBibite() for proper behavior
        /// (ExplodeToMeat if already dead, handles eggs via hatching.Abort()).
        /// </summary>
        /// <param name="callback">Called with action result on main thread</param>
        public void KillTarget(Action<ActionResult> callback)
        {
            EnqueueCommand(() =>
            {
                GameObject target = UserControl.Instance.target;

                if (target == null)
                {
                    Plugin.Logger.LogWarning("KillTarget: No target selected");
                    callback(ActionResult.Failure("kill", "No target selected"));
                    return;
                }

                try
                {
                    GUIManager.Instance.StatsPanel.KillCurrentBibite();
                    Plugin.Logger.LogInfo($"KillTarget: Executed kill via StatsPanel");
                    callback(ActionResult.Success("kill"));
                }
                catch (Exception ex)
                {
                    Plugin.Logger.LogError($"KillTarget: Exception - {ex.Message}");
                    callback(ActionResult.Failure("kill", $"Exception: {ex.Message}"));
                }
            });
        }

        /// <summary>
        /// Force target to lay an egg with specified lineage tag.
        /// Uses game's BibiteStatsPanel methods for proper TagsManager integration
        /// and UI refresh. No validation - divine intervention works on any target.
        /// </summary>
        /// <param name="lineageTag">Tag to assign to parent before reproduction</param>
        /// <param name="callback">Called with action result on main thread</param>
        public void LayTarget(string lineageTag, Action<ActionResult> callback)
        {
            EnqueueCommand(() =>
            {
                GameObject target = UserControl.Instance.target;

                if (target == null)
                {
                    Plugin.Logger.LogWarning("LayTarget: No target selected");
                    callback(ActionResult.Failure("lay", "No target selected"));
                    return;
                }

                try
                {
                    // Set lineage tag via StatsPanel (integrates with TagsManager, refreshes UI)
                    GUIManager.Instance.StatsPanel.tagInputField.text = lineageTag;
                    GUIManager.Instance.StatsPanel.UpdateSpeciesTag();
                    Plugin.Logger.LogInfo($"LayTarget: Set lineage tag to '{lineageTag}'");

                    // Execute reproduction via StatsPanel
                    GUIManager.Instance.StatsPanel.LayEggFromCurrentBibite();
                    Plugin.Logger.LogInfo("LayTarget: Reproduction executed");

                    callback(ActionResult.Success("lay"));
                }
                catch (Exception ex)
                {
                    Plugin.Logger.LogError($"LayTarget: Exception - {ex.Message}");
                    callback(ActionResult.Failure("lay", $"Exception: {ex.Message}"));
                }
            });
        }

        /// <summary>
        /// Zoom camera in or out.
        /// </summary>
        /// <param name="direction">"in" or "out"</param>
        /// <param name="callback">Called with action result on main thread</param>
        public void Zoom(string direction, Action<ActionResult> callback)
        {
            EnqueueCommand(() =>
            {
                try
                {
                    Camera mainCamera = Camera.main;
                    if (mainCamera == null)
                    {
                        Plugin.Logger.LogError("Zoom: Main camera not found");
                        callback(ActionResult.Failure("zoom", "Main camera not found"));
                        return;
                    }

                    float currentSize = mainCamera.orthographicSize;
                    float newSize;

                    if (direction == "in")
                    {
                        // Zoom in: decrease orthographic size by 10%
                        newSize = currentSize * 0.9f;
                    }
                    else if (direction == "out")
                    {
                        // Zoom out: increase orthographic size by 10%
                        newSize = currentSize * 1.1f;
                    }
                    else
                    {
                        Plugin.Logger.LogWarning($"Zoom: Invalid direction '{direction}'");
                        callback(ActionResult.Failure("zoom", $"Invalid direction: {direction}"));
                        return;
                    }

                    // Apply bounds (min 5, max depends on simulation size but typically ~250+)
                    newSize = Mathf.Clamp(newSize, 5f, 500f);
                    mainCamera.orthographicSize = newSize;

                    Plugin.Logger.LogInfo($"Zoom: {direction} - {currentSize:F1} -> {newSize:F1}");
                    callback(ActionResult.Success("zoom"));
                }
                catch (Exception ex)
                {
                    Plugin.Logger.LogError($"Zoom: Exception - {ex.Message}");
                    callback(ActionResult.Failure("zoom", $"Exception: {ex.Message}"));
                }
            });
        }

        /// <summary>
        /// Set info panel visibility (0 = close all, 1-4 = specific panels).
        /// </summary>
        /// <param name="panel">Panel number (0-4)</param>
        /// <param name="callback">Called with action result on main thread</param>
        public void SetInfoPanel(int panel, Action<ActionResult> callback)
        {
            EnqueueCommand(() =>
            {
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
                        // Close all panels
                        GUIManager.Instance.CloseAllPanels();
                        Plugin.Logger.LogInfo("SetInfoPanel: Closed all panels");
                    }
                    else
                    {
                        // Map panel numbers to BibitePanels enum
                        BibitePanels targetPanel;
                        switch (panel)
                        {
                            case 1:
                                targetPanel = BibitePanels.StatsPanel;
                                break;
                            case 2:
                                targetPanel = BibitePanels.GenesPanel;
                                break;
                            case 3:
                                targetPanel = BibitePanels.BiologyPanel;
                                break;
                            case 4:
                                targetPanel = BibitePanels.BrainPanel;
                                break;
                            default:
                                Plugin.Logger.LogWarning($"SetInfoPanel: Invalid panel {panel}");
                                callback(ActionResult.Failure("info_panel", $"Invalid panel: {panel}"));
                                return;
                        }

                        GUIManager.Instance.OpenBibitePanel(targetPanel);
                        Plugin.Logger.LogInfo($"SetInfoPanel: Opened panel {panel} ({targetPanel})");
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
