local number = 1;

function onCreate()
        setPropertyFromClass('flixel.FlxG', 'mouse.visible', true);
end

function onUpdate()
            if number == 1 then
	runHaxeCode([[
		FlxG.mouse.unload();
		FlxG.mouse.load(Paths.image("cursor/mouse (1)").bitmap);
	]])
        number = 2
            elseif number == 2 then
	runHaxeCode([[
		FlxG.mouse.unload();
		FlxG.mouse.load(Paths.image("cursor/mouse (2)").bitmap);
	]])
        number = 3
            elseif number == 3 then
	runHaxeCode([[
		FlxG.mouse.unload();
		FlxG.mouse.load(Paths.image("cursor/mouse (3)").bitmap);
	]])
        number = 4
            elseif number == 4 then
	runHaxeCode([[
		FlxG.mouse.unload();
		FlxG.mouse.load(Paths.image("cursor/mouse (4)").bitmap);
	]])
        number = 5
            elseif number == 5 then
	runHaxeCode([[
		FlxG.mouse.unload();
		FlxG.mouse.load(Paths.image("cursor/mouse (5)").bitmap);
	]])
        number = 6
            elseif number == 6 then
	runHaxeCode([[
		FlxG.mouse.unload();
		FlxG.mouse.load(Paths.image("cursor/mouse (6)").bitmap);
	]])
        number = 7
            elseif number == 7 then
	runHaxeCode([[
		FlxG.mouse.unload();
		FlxG.mouse.load(Paths.image("cursor/mouse (7)").bitmap);
	]])
        number = 8
            elseif number == 8 then
	runHaxeCode([[
		FlxG.mouse.unload();
		FlxG.mouse.load(Paths.image("cursor/mouse (8)").bitmap);
	]])
        number = 9
            elseif number == 9 then
	runHaxeCode([[
		FlxG.mouse.unload();
		FlxG.mouse.load(Paths.image("cursor/mouse (9)").bitmap);
	]])
        number = 10
            elseif number == 10 then
	runHaxeCode([[
		FlxG.mouse.unload();
		FlxG.mouse.load(Paths.image("cursor/mouse (10)").bitmap);
	]])
        number = 1
        end
end

-- necessary if you want the normal mouse to show up in things like the chart editor
function onDestroy()
	setPropertyFromClass('flixel.FlxG', 'mouse.visible', false);
	runHaxeCode('FlxG.mouse.unload();')
end