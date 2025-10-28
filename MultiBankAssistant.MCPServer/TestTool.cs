using ModelContextProtocol.Server;
using System.ComponentModel;

namespace MultiBankAssistant.MCPServer;

[McpServerToolType]
public class TestTool
{
    [McpServerTool, Description("Echoes the message back to the client.")]
    public static string Echo(string message) => $"hello {message}";
}
