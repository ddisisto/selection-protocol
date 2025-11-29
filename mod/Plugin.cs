using System;
using System.Collections.Generic;
using BepInEx;
using BepInEx.Logging;

namespace SelectionProtocol
{
    /// <summary>
    /// BepInEx plugin entry point. Manages Unity lifecycle and wires dependencies.
    /// Executes queued commands on Unity main thread via Update().
    /// </summary>
    [BepInPlugin(PluginInfo.PLUGIN_GUID, PluginInfo.PLUGIN_NAME, PluginInfo.PLUGIN_VERSION)]
    public class Plugin : BaseUnityPlugin
    {
        internal static new ManualLogSource Logger;

        private GameController _gameController;
        private ApiHandlers _apiHandlers;
        private HttpApi _httpApi;

        // Command queue: background thread (HTTP) -> main thread (Unity)
        private readonly Queue<Action> _commandQueue = new Queue<Action>();
        private readonly object _queueLock = new object();

        private void Awake()
        {
            Logger = base.Logger;
            Logger.LogInfo($"Plugin {PluginInfo.PLUGIN_GUID} v{PluginInfo.PLUGIN_VERSION} is loaded!");

            // Wire dependencies: GameController -> ApiHandlers -> HttpApi
            _gameController = new GameController(EnqueueCommand);
            _apiHandlers = new ApiHandlers(_gameController);
            _httpApi = new HttpApi(5001, _apiHandlers);

            _httpApi.Start();
            Logger.LogInfo("HTTP API started on http://localhost:5001");
            Logger.LogInfo("Command queue initialized");
        }

        /// <summary>
        /// Unity Update() - executes on main thread every frame.
        /// Drains command queue and executes Unity API calls safely.
        /// </summary>
        private void Update()
        {
            lock (_queueLock)
            {
                while (_commandQueue.Count > 0)
                {
                    var command = _commandQueue.Dequeue();
                    try
                    {
                        command.Invoke();
                    }
                    catch (Exception ex)
                    {
                        Logger.LogError($"Command execution error: {ex.Message}");
                    }
                }
            }
        }

        /// <summary>
        /// Enqueue command to execute on Unity main thread.
        /// Called from background HTTP threads.
        /// </summary>
        private void EnqueueCommand(Action command)
        {
            lock (_queueLock)
            {
                _commandQueue.Enqueue(command);
            }
        }

        private void OnDestroy()
        {
            _httpApi?.Stop();
            Logger.LogInfo("Plugin unloaded");
        }
    }
}
