using System;
using System.IO;
using System.Reflection;
class BootstrapManager {
    static int Main(string[] args) {
        string root = Environment.GetEnvironmentVariable("SCOOP_HOME");
        if (String.IsNullOrEmpty(root)) root = Path.Combine(Environment.GetEnvironmentVariable("USERPROFILE"), ".scoop");
        for (int i = 0; i < args.Length; i++) {
            if (args[i] == "--home") root = args[++i];
            else if (args[i].StartsWith("--home=")) root = args[i].Substring(7);
        }
        Directory.CreateDirectory(root);
        File.WriteAllLines(Path.Combine(root, "arguments"), args);
        if (Environment.GetEnvironmentVariable("TEST_INSTALL_FAIL") == "1") return 23;
        string bin = Path.Combine(root, "bin");
        Directory.CreateDirectory(bin);
        foreach (string tool in new string[] { "scoop-install.exe", "sco.exe" })
            File.Copy(Assembly.GetExecutingAssembly().Location, Path.Combine(bin, tool), true);
        return 0;
    }
}
