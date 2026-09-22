using AcademyNoLag.Detection;
using Xunit;

namespace AcademyNoLag.Tests;

public class GameProfileTests
{
    [Fact]
    public void ProfileManager_ContainsAionClassicProfile()
    {
        var manager = new ProfileManager();
        var aion = manager.Profiles.FirstOrDefault(p => p.Id == "aion_classic_50");

        Assert.NotNull(aion);
        Assert.True(aion.IsAionClassic);
        Assert.Contains(2106, aion.KnownPorts);
        Assert.Contains(7777, aion.KnownPorts);
    }

    [Theory]
    [InlineData("Aion.bin", true)]
    [InlineData("aion.bin", true)]
    [InlineData("aionclassic.bin", true)]
    [InlineData("Aion.exe", true)]
    [InlineData("notepad.exe", false)]
    [InlineData("chrome.exe", false)]
    public void ProfileManager_MatchesAionProcessName(string processName, bool shouldMatch)
    {
        var manager = new ProfileManager();
        var profile = manager.FindMatchingProfile(processName);

        if (shouldMatch)
        {
            Assert.NotNull(profile);
            Assert.Equal("aion_classic_50", profile.Id);
        }
        else
        {
            Assert.Null(profile);
        }
    }
}
