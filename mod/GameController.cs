using System;

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
        /// Check if game is ready for state access (singletons initialized).
        /// </summary>
        public bool IsGameReady()
        {
            // For now, always return true. Will add actual checks when accessing game state.
            return true;
        }

        /// <summary>
        /// Queue a command to execute on Unity main thread.
        /// </summary>
        protected void EnqueueCommand(Action command)
        {
            _enqueueCommand(command);
        }
    }
}
