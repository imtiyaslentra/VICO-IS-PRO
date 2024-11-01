-- Initialization
local Stats = game:GetService('Stats')
local Players = game:GetService('Players')
local RunService = game:GetService('RunService')
local ReplicatedStorage = game:GetService('ReplicatedStorage')
local Workspace = game:GetService('Workspace')
local CoreGui = game:GetService('CoreGui')
local UserInputService = game:GetService("UserInputService")

local Nurysium_Util = loadstring(game:HttpGet("https://raw.githubusercontent.com/flezzpe/Nurysium/main/nurysium_helper.lua"))()

-- Player and Camera
local local_player = Players.LocalPlayer
local camera = Workspace.CurrentCamera

-- Global Variables
getgenv().aura_Enabled = false
getgenv().hit_sound_Enabled = false
getgenv().hit_effect_Enabled = false
getgenv().optimize_Enabled = false
getgenv().autoSpam_Enabled = false
getgenv().antiCurve_Enabled = false
getgenv().visualizer_Enabled = false

-- Learning Data Initialization
local learningData = {
    failedAttempts = 0,
    successfulParries = 0,
    lastFailureTime = 0,
    lastSuccessTime = 0
}

-- Library UI Initialization
task.wait(1)
local main = library.new()
local tab = main.create_tab('Main')
local tab1 = main.create_tab('Optimize')
local tab2 = main.create_tab('Visual')

-- Utility Functions
local nurysium_Data = nil
local hit_Sound = nil
local closest_Entity = nil
local parry_remote = nil

local function initialize_hit_sound(dataFolder_name)
    nurysium_Data = Instance.new('Folder', CoreGui)
    nurysium_Data.Name = dataFolder_name

    hit_Sound = Instance.new('Sound', nurysium_Data)
    hit_Sound.SoundId = 'rbxassetid://8632670510'
    hit_Sound.Volume = 5
end

local function get_closest_entity(object)
    local closest
    local max_distance = math.huge

    for _, entity in pairs(Workspace:FindFirstChild('Alive'):GetChildren()) do
        if entity:IsA('Model') and entity:FindFirstChild('HumanoidRootPart') and entity.Name ~= local_player.Name then
            local distance = (object.Position - entity.HumanoidRootPart.Position).Magnitude
            if distance < max_distance then
                closest_Entity = entity
                max_distance = distance
            end
        end
    end

    return closest_Entity
end

local function resolve_parry_remote()
    local services = {
        game:GetService('AdService'),
        game:GetService('SocialService')
    }

    for _, service in pairs(services) do
        local temp_remote = service:FindFirstChildOfClass('RemoteEvent')

        if temp_remote and temp_remote.Name:find('\n') then
            parry_remote = temp_remote
            break
        end
    end
end

-- Event Handlers
if ReplicatedStorage:FindFirstChild('Remotes') and ReplicatedStorage.Remotes:FindFirstChild('ParrySuccess') then
    ReplicatedStorage.Remotes.ParrySuccess.OnClientEvent:Connect(function()
        if getgenv().hit_sound_Enabled then
            hit_Sound:Play()
        end

        if getgenv().hit_effect_Enabled then
            local hit_effect = game:GetObjects("rbxassetid://17407244385")[1]
            if hit_effect then
                hit_effect.Parent = Nurysium_Util.getBall()
                hit_effect:Emit(4)

                task.delay(5, function()
                    if hit_effect and hit_effect.Parent then
                        hit_effect:Destroy()
                    end
                end)
            end
        end

        learningData.successfulParries = learningData.successfulParries + 1
        learningData.lastSuccessTime = tick()
    end)
else
    warn("ReplicatedStorage.Remotes.ParrySuccess not found.")
end

local aura_table = {
    canParry = true,
    is_Spamming = false,
    parry_Range = 0,
    spam_Range = 0,
    hit_Count = 0,
    hit_Time = tick(),
}

if ReplicatedStorage:FindFirstChild('Remotes') and ReplicatedStorage.Remotes:FindFirstChild('ParrySuccessAll') then
    ReplicatedStorage.Remotes.ParrySuccessAll.OnClientEvent:Connect(function()
        aura_table.hit_Count = aura_table.hit_Count + 1
        task.delay(0.15, function()
            aura_table.hit_Count = aura_table.hit_Count - 1
        end)
    end)
else
    warn("ReplicatedStorage.Remotes.ParrySuccessAll not found.")
end

if Workspace:FindFirstChild("Balls") then
    Workspace.Balls.ChildRemoved:Connect(function(child)
        aura_table.hit_Count = 0
        aura_table.is_Spamming = false
    end)
else
    warn("Workspace.Balls not found.")
end

-- Visualizer Functions
local visualizer
local originalSize = 10
local maxSize = 100

local function createVisualizer()
    if visualizer then
        visualizer:Destroy()
    end

    visualizer = Instance.new("Part")
    visualizer.Shape = Enum.PartType.Ball
    visualizer.Size = Vector3.new(originalSize, originalSize, originalSize)
    visualizer.Anchored = true
    visualizer.CanCollide = false
    visualizer.Material = Enum.Material.ForceField
    visualizer.BrickColor = BrickColor.new("Bright green")
    visualizer.Transparency = 0.7
    visualizer.Parent = Workspace

    RunService.Heartbeat:Connect(function()
        if visualizer and local_player and local_player.Character and local_player.Character.PrimaryPart then
            visualizer.CFrame = local_player.Character.PrimaryPart.CFrame
        end
    end)
end

local function updateVisualizerSize(ball_Speed)
    if visualizer then
        local newSize = math.clamp(originalSize + (ball_Speed / 100), originalSize, maxSize)
        visualizer.Size = Vector3.new(newSize, newSize, newSize)
        aura_table.parry_Range = newSize * 10
    end
end

local function updateVisualizer(isTargeted)
    if visualizer then
        visualizer.BrickColor = isTargeted and BrickColor.new("Bright red") or BrickColor.new("Bright green")
    end
end

-- Enhanced Auto-Spam Function
local autoSpam_Threshold = 20
local speed_Check_Interval = 0.1
local autoSpam_Detection_Threshold = 15 -- Threshold for detecting spam

local function updateAutoSpamBasedOnSpeedAndDistance()
    local self = Nurysium_Util.getBall()
    if not self then
        return
    end

    local ball_Velocity = self.AssemblyLinearVelocity
    local ball_Speed = ball_Velocity.Magnitude
    local ball_Position = self.Position
    local player_Position = local_player.Character.PrimaryPart.Position
    local ball_Distance = (player_Position - ball_Position).Magnitude

    -- Update auto spam settings based on speed and distance
    local min_Speed_Threshold = 20
    local min_Distance_Threshold = 10

    if ball_Speed > min_Speed_Threshold and ball_Distance < min_Distance_Threshold then
        aura_table.is_Spamming = true
    else
        aura_table.is_Spamming = false
    end
end

task.spawn(function()
    while true do
        if getgenv().autoSpam_Enabled then
            updateAutoSpamBasedOnSpeedAndDistance()

            local hit_Count = aura_table.hit_Count
            local hit_Threshold = 2

            if hit_Count > hit_Threshold then
                aura_table.is_Spamming = true
            end

            local self = Nurysium_Util.getBall()
            if self then
                updateVisualizerSize(self.AssemblyLinearVelocity.Magnitude)
            end
        end
        task.wait(speed_Check_Interval)
    end
end)

-- Adaptive Auto Parry Logic
local function predictParryPosition(ball_Position, ball_Velocity, ping)
    local timeToImpact = (ball_Position - local_player.Character.PrimaryPart.Position).Magnitude / ball_Velocity.Magnitude
    local predicted_Position = ball_Position + (ball_Velocity * timeToImpact)
    return predicted_Position
end

task.spawn(function()
    RunService.PreRender:Connect(function()
        if not getgenv().aura_Enabled then
            return
        end

        if closest_Entity then
            local entity_root = Workspace:FindFirstChild('Alive'):FindFirstChild(closest_Entity.Name)
            if entity_root and entity_root:FindFirstChild('Humanoid') and entity_root.Humanoid.Health > 0 then
                if aura_table.is_Spamming then
                    if local_player:DistanceFromCharacter(closest_Entity.HumanoidRootPart.Position) <= aura_table.spam_Range then
                        if parry_remote then
                            local target_position = closest_Entity.HumanoidRootPart.Position
                            if getgenv().antiCurve_Enabled then
                                target_position = camera.CFrame.Position + (target_position - camera.CFrame.Position).Unit * (local_player:DistanceFromCharacter(target_position) - 5)
                            end
                            parry_remote:FireServer(
                                0.5,
                                CFrame.new(camera.CFrame.Position, Vector3.zero),
                                {[closest_Entity.Name] = target_position},
                                {target_position.X, target_position.Y},
                                false
                            )
                        end
                    end
                end
            end
        end
    end)

    RunService.PreRender:Connect(function()
        if not getgenv().aura_Enabled then
            return
        end

        local ping = Stats.Network.ServerStatsItem['Data Ping']:GetValue() / 10
        local self = Nurysium_Util.getBall()

        if not self then
            return
        end

        self:GetAttributeChangedSignal('target'):Once(function()
            aura_table.canParry = true
        end)

        if getgenv().visualizer_Enabled then
            updateVisualizer(self:GetAttribute('target') == local_player.Name)
            local ball_Velocity = self.AssemblyLinearVelocity
            updateVisualizerSize(ball_Velocity.Magnitude)
        end

        if self:GetAttribute('target') ~= local_player.Name or not aura_table.canParry then
            return
        end

        get_closest_entity(local_player.Character.PrimaryPart)

        local player_Position = local_player.Character.PrimaryPart.Position
        local ball_Position = self.Position
        local ball_Velocity = self.AssemblyLinearVelocity

        local ball_Direction = (player_Position - ball_Position).Unit
        local ball_Distance = local_player:DistanceFromCharacter(ball_Position)
        local ball_Speed = ball_Velocity.Magnitude

        local predicted_Target_Position = predictParryPosition(ball_Position, ball_Velocity, ping)
        local parry_Distance = math.max(math.max(ping, 4) + ball_Speed / 3.5, 9.5)
        local parry_Position = camera.CFrame.Position + (ball_Direction * parry_Distance)

        aura_table.spam_Range = math.max(ping / 10, 15) + ball_Speed / 7
        aura_table.parry_Range = parry_Distance
        aura_table.is_Spamming = aura_table.hit_Count > 1 or ball_Distance < 13.5

        if ball_Distance <= aura_table.parry_Range and not aura_table.is_Spamming then
            if parry_remote then
                local target_position = predicted_Target_Position
                if getgenv().antiCurve_Enabled then
                    target_position = camera.CFrame.Position + (target_position - camera.CFrame.Position).Unit * (local_player:DistanceFromCharacter(target_position) - 5)
                end
                parry_remote:FireServer(
                    0.5,
                    CFrame.new(camera.CFrame.Position, target_position),
                    {[closest_Entity.Name] = target_position},
                    {target_position.X, target_position.Y},
                    false
                )
            end

            aura_table.canParry = false
            aura_table.hit_Time = tick()
            aura_table.hit_Count = aura_table.hit_Count + 1

            task.delay(0.15, function()
                aura_table.hit_Count = aura_table.hit_Count - 1
            end)
        end

        task.spawn(function()
            repeat
                RunService.PreRender:Wait()
            until (tick() - aura_table.hit_Time) >= 1
            aura_table.canParry = true
        end)
    end)
end)

initialize_hit_sound('nurysium_temp')

print("hello lovely skidder its me kia_ainsleyy")

local UserInputService = game:GetService("UserInputService");

local Library = loadstring(game:HttpGet("https://raw.githubusercontent.com/lxte/lates-lib/main/Main.lua"))()
local Window = Library:CreateWindow({
	Title = "Vico - Blade ball",
	Theme = "Dark",
	
	Size = UDim2.fromOffset(570, 370),
	Transparency = 0.2,
	Blurring = true,
	MinimizeKeybind = Enum.KeyCode.LeftAlt,
})

local Themes = {
	Light = {
		--// Frames:
		Primary = Color3.fromRGB(232, 232, 232),
		Secondary = Color3.fromRGB(255, 255, 255),
		Component = Color3.fromRGB(245, 245, 245),
		Interactables = Color3.fromRGB(235, 235, 235),

		--// Text:
		Tab = Color3.fromRGB(50, 50, 50),
		Title = Color3.fromRGB(0, 0, 0),
		Description = Color3.fromRGB(100, 100, 100),

		--// Outlines:
		Shadow = Color3.fromRGB(255, 255, 255),
		Outline = Color3.fromRGB(210, 210, 210),

		--// Image:
		Icon = Color3.fromRGB(100, 100, 100),
	},
	
	Dark = {
		--// Frames:
		Primary = Color3.fromRGB(30, 30, 30),
		Secondary = Color3.fromRGB(35, 35, 35),
		Component = Color3.fromRGB(40, 40, 40),
		Interactables = Color3.fromRGB(45, 45, 45),

		--// Text:
		Tab = Color3.fromRGB(200, 200, 200),
		Title = Color3.fromRGB(240,240,240),
		Description = Color3.fromRGB(200,200,200),

		--// Outlines:
		Shadow = Color3.fromRGB(0, 0, 0),
		Outline = Color3.fromRGB(40, 40, 40),

		--// Image:
		Icon = Color3.fromRGB(220, 220, 220),
	},
	
	Void = {
		--// Frames:
		Primary = Color3.fromRGB(15, 15, 15),
		Secondary = Color3.fromRGB(20, 20, 20),
		Component = Color3.fromRGB(25, 25, 25),
		Interactables = Color3.fromRGB(30, 30, 30),

		--// Text:
		Tab = Color3.fromRGB(200, 200, 200),
		Title = Color3.fromRGB(240,240,240),
		Description = Color3.fromRGB(200,200,200),

		--// Outlines:
		Shadow = Color3.fromRGB(0, 0, 0),
		Outline = Color3.fromRGB(40, 40, 40),

		--// Image:
		Icon = Color3.fromRGB(220, 220, 220),
	},

}

--// Set the default theme
Window:SetTheme(Themes.Dark)

--// Sections
Window:AddTabSection({
	Name = "Main",
	Order = 1,
})

--// Tab [MAIN]

local AAA = Window:AddTab({
	Title = "Info",
	Section = "Vico Hub",
	Icon = "rbxassetid://11963373994"
})

Window:AddSection({ Name = "Information", Tab = AAA }) 


Window:AddParagraph({
	Title = "🧏 Vico - Blade ball 💥",
	Description = "Be careful Vico will grow",
	Tab = AAA
})
				
	Window:AddParagraph({
	Title = "[] Vico Credit []",
	Description = "Rudert",
	Tab = AAA
})		

Window:AddToggle({
	Title = "Rudert Discord Link!",
	Description = "https://discord.gg/EwARkGncq4",
	Tab = AAA,
	Callback = function()
		setclipboard("https://discord.gg/EwARkGncq4")
	end,
}) 

Window:AddToggle({
	Title = "Rudert Youtube Link!",
	Description = "https://youtube.com/@starx575",
	Tab = AAA,
	Callback = function()
		setclipboard("https://youtube.com/@starx575")
	end,
}) 
				
local Main = Window:AddTab({
	Title = "Main",
	Section = "Main",
	Icon = "rbxassetid://11963373994"
})
				
Window:AddSection({ Name = "Autoparry", Tab = Main }) 


Window:AddToggle({
	Title = "• Autoparry",
	Description = "\/ Parrys the ball [Still build up but 90%] /\",
	Tab = Main,
	Callback = function(state)
	getgenv().aura_Enabled = state

	end,
}) 

Window:AddToggle({
	Title = "• Autospam",
	Description = "\/ Toggles Autospam when near player(only works on clash) /\",
	Tab = Main,
	Callback = function(state)
	
		getgenv().autoSpam_Enabled = state
	end,
}) 

Window:AddSection({ Name = "Parry Misc", Tab = Main }) 
					
		Window:AddToggle({
	Title = "• Anti Spam Curve",
	Description = "\/ When spamming/parry it Will detect it /\",
	Tab = Main,
	Callback = function(state)
        getgenv().antiCurve_Enable = state
	end,
})	
				
Window:AddSection({ Name = "Debug", Tab = Main }) 
	
				Window:AddToggle({
	Title = "• Visualizer",
	Description = "\/ Show Parry And Spam Range /\",
	Tab = Main,
	Callback = function(state)
visualize_Enabled = state
	end,
})										
				
--// Tab [SETTINGS]
local Keybind = nil
local Settings = Window:AddTab({
	Title = "Settings",
	Section = "Settings",
	Icon = "rbxassetid://11293977610",
})


Window:AddDropdown({
	Title = "Set Theme",
	Description = "Set the theme of the library! Amazing Right?",
	Tab = Settings,
	Options = {
		["Light Mode"] = "Light",
		["Dark Mode"] = "Dark",
		["Extra Dark"] = "Void",
	},
	Callback = function(Theme) 
		Window:SetTheme(Themes[Theme])
	end,
}) 

Window:AddToggle({
	Title = "UI Blur",
	Description = "If enabled, must have your Roblox graphics set to 8+ for it to work",
	Default = true,
	Tab = Settings,
	Callback = function(Boolean) 
		Window:SetSetting("Blur", Boolean)
	end,
}) 


Window:AddSlider({
	Title = "UI Transparency",
	Description = "Set the transparency of the UI(0.15/0.20 Recommended)",
	Tab = Settings,
	AllowDecimals = true,
	MaxValue = 1,
	Callback = function(Amount) 
		Window:SetSetting("Transparency", Amount)
	end,
}) 

Window:Notify({
	Title = "hey How about my script? hope you're not bored :)",
	Description = "Press Left Alt or The Image To Minimize The Window.", 
	Duration = 10
})

-- Start the check in a new thread
spawn(detectAutoSpam)

local ScreenGui = Instance.new("ScreenGui")
local ImageButton = Instance.new("ImageButton")
local UICorner = Instance.new("UICorner")

local notificationShown = true -- Status untuk notifikasi

-- Fungsi gabungan untuk mendeteksi dan menampilkan notifikasi spam
local function detectAutoSpam()
    local spamCount = 0
    local autoSpamDetected = false

    while true do
        task.wait(speed_Check_Interval)

        if aura_table.is_Spamming then
            spamCount = spamCount + 1
            if spamCount > autoSpam_Detection_Threshold and not autoSpamDetected then
                -- Menampilkan notifikasi ketika spam terdeteksi
                if notificationShown then
                    -- Pastikan 'Window' didefinisikan sebelumnya atau ganti dengan metode notifikasi lain
                    Window:Notify({
                        Title = "Detected Spam!?",
                        Description = "Spam will be active because it has been fulfilled.",
                        Duration = 3
                    })
                    notificationShown = false -- Matikan notifikasi setelah ditampilkan
                end
                autoSpamDetected = true -- Tandai bahwa spam telah terdeteksi
            end
        else
            spamCount = 0
            autoSpamDetected = false -- Reset deteksi setelah spam berakhir
            notificationShown = true -- Siapkan notifikasi untuk deteksi berikutnya
        end
    end
end
            
-- Configure the ScreenGui
ScreenGui.Parent = game.CoreGui
ScreenGui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling

-- Configure the ImageButton
ImageButton.Parent = ScreenGui
ImageButton.BackgroundColor3 = Color3.fromRGB(0, 0, 0)
ImageButton.BorderSizePixel = 0
ImageButton.Position = UDim2.new(0.120833337, 0, 0.0952890813, 0)
ImageButton.Size = UDim2.new(0, 50, 0, 50)
ImageButton.Image = "rbxassetid://15302652530" -- Set the image using the decal ID
ImageButton.Draggable = true

-- Add UICorner for rounded corners
UICorner.Parent = ImageButton

-- Function to handle click event
ImageButton.MouseButton1Click:Connect(function()
    game:GetService("VirtualInputManager"):SendKeyEvent(true, Enum.KeyCode.LeftAlt, false, game)
end)
print("Loading Succesful!")
wait(1)
print("Credit To Rudert 😎")
wait(1)
print("This Is Gonna Blow Up 💥😹")

--Execute Checker  
loadstring(game:HttpGet("https://raw.githubusercontent.com/StarX-exploit/executed/refs/heads/main/exe.lua"))()
print("Succesfull Checking Execute")
wait(2)
print("Spam Update! ,spam will be 5x faster and that's already very OP")

local function optimizePerformance()
    -- Boost FPS by disabling unnecessary features and reducing settings
    game:GetService("Workspace").StreamingEnabled = true
    settings().Rendering.QualityLevel = Enum.QualityLevel.Level01 -- Lowest quality for best FPS
    game:GetService("Lighting").GlobalShadows = false -- Disable shadows
    game:GetService("Lighting").Brightness = 2 -- Adjust lighting for smoothness
    game:GetService("UserInputService").MouseDeltaSensitivity = 0.5 -- Reduce mouse lag
    setfpscap(999) -- Increase FPS cap to 120 for smoother performance
    
    -- Optimize memory usage
    local function optimizeMemoryUsage()
        local serviceMemoryLimits = {
            ['Players'] = 2048,
            ['Workspace'] = 2048,
            ['ReplicatedStorage'] = 2048,
            -- Add more services as needed
        }

        for serviceName, limit in pairs(serviceMemoryLimits) do
            local service = game:GetService(serviceName)
            if service then
                -- Assuming there is a method to set memory limit
                -- Uncomment if such a method exists
                -- service:SetMemoryLimit(limit)
            end
        end
    end
    optimizeMemoryUsage()
end

optimizePerformance() -- Call the performance optimization function
print("Performance optimization is complete.")

-- Adaptive Learning Function
local function adaptStrategy()
    if tick() - learningData.lastFailureTime < 60 then
        autoSpam_Threshold = autoSpam_Threshold * 0.9 -- Decrease threshold for more aggressive auto-spam
    elseif tick() - learningData.lastSuccessTime > 300 then
        autoSpam_Threshold = autoSpam_Threshold * 1.1 -- Increase threshold to reduce aggressive auto-spam
    end

    learningData.failedAttempts = 0
end

-- Track failures
task.spawn(function()
    while true do
        adaptStrategy()
        task.wait(10) -- Adjust learning frequency
    end
end)

-- Start auto-spam detection
task.spawn(detectAutoSpam)