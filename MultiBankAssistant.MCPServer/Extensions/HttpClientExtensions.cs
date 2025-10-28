namespace MultiBankAssistant.MCPServer.Extensions;

public static class HttpClientExtensions
{
    public static WebApplicationBuilder AddIntegrationSettings(this WebApplicationBuilder builder)
    {
        var settings = new IntegrationSettings();
        builder.Configuration.GetSection("IntegrationSettings").Bind(settings);

      
        builder.Services.AddHttpClient("BankA", client =>
        {
            client.BaseAddress = new Uri(settings.VBankUrl);
            client.DefaultRequestHeaders.Add("Accept", "application/json"); // мб сюда хедеры авторизации сразу прокинуть?
        });
        builder.Services.AddHttpClient("BankB", client =>
        {
            client.BaseAddress = new Uri(settings.ABankUrl);
            client.DefaultRequestHeaders.Add("Accept", "application/json"); 
        {
            client.BaseAddress = new Uri(settings.SBankUrl);
            client.DefaultRequestHeaders.Add("Accept", "application/json"); 
        });


        return builder;
    }

}
