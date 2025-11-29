using BepInEx;
using BepInEx.Logging;

namespace SelectionProtocol
{
    [BepInPlugin(PluginInfo.PLUGIN_GUID, PluginInfo.PLUGIN_NAME, PluginInfo.PLUGIN_VERSION)]
    public class Plugin : BaseUnityPlugin
    {
        internal static new ManualLogSource Logger;

        private HttpApi _httpApi;

        private void Awake()
        {
            Logger = base.Logger;
            Logger.LogInfo($"Plugin {PluginInfo.PLUGIN_GUID} v{PluginInfo.PLUGIN_VERSION} is loaded!");

            // Start HTTP API server
            _httpApi = new HttpApi(5001);
            _httpApi.Start();

            Logger.LogInfo("HTTP API started on http://localhost:5001");
        }

        private void OnDestroy()
        {
            // Clean up HTTP server on plugin unload
            _httpApi?.Stop();
            Logger.LogInfo("Plugin unloaded");
        }
    }
}
