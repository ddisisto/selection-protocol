using System;
using BepInEx;
using BepInEx.Logging;

namespace SelectionProtocol
{
    /// <summary>
    /// BepInEx plugin entry point. Manages Unity lifecycle and wires dependencies.
    /// </summary>
    [BepInPlugin(PluginInfo.PLUGIN_GUID, PluginInfo.PLUGIN_NAME, PluginInfo.PLUGIN_VERSION)]
    public class Plugin : BaseUnityPlugin
    {
        internal static new ManualLogSource Logger;

        private GameController _gameController;
        private ApiHandlers _apiHandlers;
        private HttpApi _httpApi;

        private void Awake()
        {
            Logger = base.Logger;
            Logger.LogInfo($"Plugin {PluginInfo.PLUGIN_GUID} v{PluginInfo.PLUGIN_VERSION} is loaded!");

            // Wire dependencies: GameController -> ApiHandlers -> HttpApi
            _gameController = new GameController(DummyEnqueueCommand);
            _apiHandlers = new ApiHandlers(_gameController);
            _httpApi = new HttpApi(5001, _apiHandlers);

            _httpApi.Start();
            Logger.LogInfo("HTTP API started on http://localhost:5001");
        }

        private void OnDestroy()
        {
            _httpApi?.Stop();
            Logger.LogInfo("Plugin unloaded");
        }

        // Temporary dummy method (will be replaced with actual queue in commit 2)
        private void DummyEnqueueCommand(Action command)
        {
            Logger.LogWarning("Command queue not yet implemented");
        }
    }
}
