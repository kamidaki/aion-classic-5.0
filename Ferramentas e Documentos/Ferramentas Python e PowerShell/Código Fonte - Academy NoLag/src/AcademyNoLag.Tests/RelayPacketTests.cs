using System.Text;
using AcademyNoLag.Relay.Protocol;
using Xunit;

namespace AcademyNoLag.Tests;

public class RelayPacketTests
{
    [Fact]
    public void EncodeAndDecode_ValidPacket_RoundtripsSuccessfully()
    {
        uint sessionId = 0x12345678;
        byte[] payload = Encoding.UTF8.GetBytes("AcademyNoLag Aion Classic Packet Payload Test");

        byte[] encoded = RelayPacket.Encode(RelayCommand.Data, sessionId, payload);
        bool success = RelayPacket.TryDecode(encoded, out var decoded);

        Assert.True(success);
        Assert.NotNull(decoded);
        Assert.Equal(RelayCommand.Data, decoded.Command);
        Assert.Equal(sessionId, decoded.SessionId);
        Assert.Equal(payload, decoded.Payload);
    }

    [Fact]
    public void TryDecode_CorruptedPayload_FailsCrcValidation()
    {
        uint sessionId = 0x87654321;
        byte[] payload = [1, 2, 3, 4, 5, 6, 7, 8];

        byte[] encoded = RelayPacket.Encode(RelayCommand.Data, sessionId, payload);

        // Corrupt a byte in payload
        encoded[^1] ^= 0xFF;

        bool success = RelayPacket.TryDecode(encoded, out var decoded);
        Assert.False(success);
        Assert.Null(decoded);
    }
}
