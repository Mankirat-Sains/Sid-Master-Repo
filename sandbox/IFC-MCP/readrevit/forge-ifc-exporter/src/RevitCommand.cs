using DesignAutomationFramework;
using Autodesk.Revit.DB;
using System.IO;

public class IFCExportAutomation : IExternalDBApplication
{
    public ExternalDBApplicationResult OnStartup(ControlledApplication app)
    {
        DesignAutomationBridge.DesignAutomationReadyEvent += Run;
        return ExternalDBApplicationResult.Succeeded;
    }

    public ExternalDBApplicationResult OnShutdown(ControlledApplication app)
    {
        return ExternalDBApplicationResult.Succeeded;
    }

    private void Run(object sender, DesignAutomationReadyEventArgs e)
    {
        var data = e.DesignAutomationData;
        var app = data.RevitApp;
        var doc = app.OpenDocumentFile(data.FilePath);

        string outDir = Path.GetDirectoryName(data.FilePath);
        string outFile = Path.Combine(outDir, "output.ifc");

        IFCExportOptions options = new IFCExportOptions();

        doc.Export(outDir, "output.ifc", options);

        doc.Close(false);
    }
}

