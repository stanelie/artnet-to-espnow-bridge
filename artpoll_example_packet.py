artpoll reply example packet :

 else if (e.Packet.OpCode == ArtNet.Enums.ArtNetOpCodes.Poll)
       {

           int settingsUniverse = DBFunctions.SettingValues.StartingUniverse;
           byte universe = (byte)(settingsUniverse & 0x000f);
           byte subnet = (byte)(((settingsUniverse - universe) >> 4) & 0xf);
           byte net = (byte)(settingsUniverse >> 8);
           int neededUniverses = ((frmInterface)Program.frmInterface).GetUniverseCount();

           byte[] ipAddressArray = ipAddress.GetAddressBytes();
           byte[] packetData = {
               0x41, 0x72, 0x74, 0x2d, 0x4e, 0x65, 0x74, 0x00, // 0-7 "Art-Net"
               0x00, 0x21, // 8-9 OpCode (ArtPollReply)
               //  10-13 IP ADDRESS
               ipAddressArray[0], ipAddressArray[1], ipAddressArray[2], ipAddressArray[3],
               0x36, 0x19, // 14-15 Port-Address
               0x01, 0x40, // 16-17 hi lo VersInfo
               net,       // 18 NetSwitch
               subnet,       // 19 SubSwitch
               0x20, 0x60, // 20-21 OemHi, Lo
               0x00,       // 22 Ubea version #
               0x10,       // 23 Status 1 (configuration bits)
               0x4c, 0x41, // 24-25 lo hi ESTA manufacturer code
               // Short name 26-43 (18 bytes)
               0x41, 0x72, 0x74, 0x6E, 0x65, 0x74, 0x32, 0x54, 0x77, 0x69, 0x6E, 0x6B, 0x6C, 0x79, 0x00, 0x00, 0x00, 0x00, //Artnet2Twinkly
               // Long name 44-107(64 bytes)
               0x41, 0x72, 0x74, 0x6E, 0x65, 0x74, 0x32, 0x54, 0x77, 0x69, 0x6E, 0x6B, 0x6C, 0x79, 0x00, 0x00, 0x00, 0x00, //Artnet2Twinkly
               0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
               0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
               0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
               // Node Report 108-171 (64 bytes)
               0x23, 0x30, 0x30, 0x30, 0x31, 0x20, 0x5b, 0x30, 0x30, 0x30, 0x30, 0x5d, 0x20, 0x41, 0x43, 0x4d, 0x45, 0x20,
               0x41, 0x72, 0x74, 0x2d, 0x4e, 0x65, 0x74, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
               0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
               0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
               // 127-173 NumPorts (2 bytes)
               0x00, 0x01,
               // 174-177 Port types (4 bytes)
               0xff, 0x00, 0x00, 0x00,
               // 178-181 GoodInput (4 bytes)
               0xff, 0xff, 0xff, 0xff,
               // 182-185 GoodOutput (4 bytes)
               0xff, 0xff, 0xff, 0xff,
               // 186-189 SwIn (4 bytes)
               0x00, 0x00, 0x00, 0x00,
               // 190-193 SwOut (4 bytes)
               universe, 0x00, 0x00, 0x00,
               // 194-196 deprecated
               0x00, 0x00, 0x00,
               // 197-199 spare
               0x00, 0x00, 0x00,
               // Style (1 byte)
               0x00,
               // MAC (6 bytes)
               0x01, 0x02, 0x03, 0x04, 0x05, 0x06,
               // BindIp (4 bytes)
               ipAddressArray[0], ipAddressArray[1], ipAddressArray[2], ipAddressArray[3],
               // BindIndex (1 byte)
               0x00,
               // Status2 (1 byte)
               0x00,
               //filler
               0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
               0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00

           };
           UdpClient client = new UdpClient();
           System.Threading.Thread.Sleep(50);
           for (int i = 0; i < neededUniverses; i++)
           {
               System.Threading.Thread.Sleep(10);
               client.Send(packetData, packetData.Length, e.Source.Address.ToString(), e.Source.Port);
               packetData[190]++;
               if (packetData[190] > 15)
               {
                   packetData[190] = 0;
                   packetData[19]++;
                   if (packetData[19] > 15)
                   {
                       packetData[19] = 0;
                       packetData[18]++;
                   }
               }
           }

       }