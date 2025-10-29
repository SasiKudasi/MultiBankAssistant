
using MultiBankAssistant.MCPServer.Extensions;

var builder = WebApplication.CreateBuilder(args);
builder.AddIntegrationSettings();
builder.Services.AddMcpServer()
    .WithHttpTransport()
    .WithToolsFromAssembly();

builder.Services.AddCors(options =>
{
    options.AddDefaultPolicy(policy =>
    {
        policy.AllowAnyOrigin()
              .AllowAnyMethod()
              .AllowAnyHeader();
    });
});

var app = builder.Build();


app.Use(async (context, next) =>
{
    //здесь можно логинится в банк
    await next();
});

app.UseCors();

if (app.Environment.IsDevelopment())
{
    app.MapOpenApi();
}
app.MapMcp("/sse");

app.MapGet("/test", () => "ЙОУ ЙОУ!");


app.Run();

