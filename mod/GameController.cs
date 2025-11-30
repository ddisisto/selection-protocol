using System;
using ManagementScripts;

namespace SelectionProtocol
{
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
    }
}
