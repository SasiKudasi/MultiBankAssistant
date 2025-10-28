using ModelContextProtocol.Server;
using Microsoft.AspNetCore.Builder;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using MultiBankAssistant.MCPServer.Extensions;

var builder = WebApplication.CreateBuilder(args);
builder.AddIntegrationSettings();
builder.Services.AddMcpServer()
    .WithHttpTransport()
    .WithToolsFromAssembly();
var app = builder.Build();

if (app.Environment.IsDevelopment())
{
    app.MapOpenApi();
}
app.MapMcp("/sse");

app.Run();

