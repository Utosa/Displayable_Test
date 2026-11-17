# Ren'Py Displayable 极简演示（直接替换 game/script.rpy 即可运行）
# 只保留核心的 3 个类 + 4 步简单实例化，一屏就能看完。

init python:
    import pygame

    # 先把默认“单按空格就跳过对话/触发按钮”的绑定去掉，
    # 不然刚按住空格就直接跳句了，来不及蓄力。
    for _name in ("dismiss", "button_select"):
        if _name in config.keymap:
            config.keymap[_name] = [k for k in config.keymap[_name] if "K_SPACE" not in k]


    # 1. 最简纯色块：搞懂 Render / render() / blit / visit
    class CustomBox(renpy.Displayable):
        def __init__(self, box_width, box_height, color="#3498db", **properties):
            super(CustomBox, self).__init__(**properties)
            self.box_width = box_width
            self.box_height = box_height
            self.color = color
            self.child = Solid(self.color)

        def render(self, width, height, st, at):
            rv = renpy.Render(self.box_width, self.box_height)
            child_render = renpy.render(self.child, self.box_width, self.box_height, st, at)
            rv.blit(child_render, (0, 0))
            return rv

        def visit(self):
            return [ self.child ]


    # 2. 长按空格推进：搞懂 redraw / timeout / return True
    class _SpaceHoldAdvance(renpy.Displayable):
        def __init__(self, hold_duration=1.0, **properties):
            super(_SpaceHoldAdvance, self).__init__(**properties)
            self.hold_duration = hold_duration
            self.is_holding = False
            self.hold_start_st = None

        def event(self, ev, x, y, st):
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_SPACE:
                if not self.is_holding:
                    self.is_holding = True
                    self.hold_start_st = st
                    renpy.redraw(self, 0)
            elif ev.type == pygame.KEYUP and ev.key == pygame.K_SPACE:
                if self.is_holding:
                    self.is_holding = False
                    self.hold_start_st = None
                    renpy.redraw(self, 0)

            if self.is_holding and self.hold_start_st is not None:
                if (st - self.hold_start_st) >= self.hold_duration:
                    self.is_holding = False
                    self.hold_start_st = None
                    return True
            return None

        def render(self, width, height, st, at):
            rv = renpy.Render(200, 20)
            # 垫一层深灰底，平时也能看清进度条在哪（嫌多余可以直接删掉下面这行）
            rv.blit(renpy.render(Solid("#333333"), 200, 20, st, at), (0, 0))

            if self.is_holding and self.hold_start_st is not None:
                elapsed = st - self.hold_start_st
                progress = min(1.0, elapsed / self.hold_duration)
                bar_width = int(200 * progress)
                if bar_width > 0:
                    bar = renpy.render(Solid("#2ecc71"), bar_width, 20, st, at)
                    rv.blit(bar, (0, 0))
                renpy.timeout(0.01)
                renpy.redraw(self, 0)
            return rv


    # 3. 实战版：支持任意 Ren'Py Action
    class SpaceHoldButton(renpy.Displayable):
        def __init__(self, hold_duration=1.0, action=None, **properties):
            super().__init__(**properties)
            self.hold_duration = hold_duration
            self.action = action
            self.is_holding = False
            self.hold_start_st = None

        def event(self, ev, x, y, st):
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_SPACE:
                if not self.is_holding:
                    self.is_holding = True
                    self.hold_start_st = st
                    renpy.redraw(self, 0)
            elif ev.type == pygame.KEYUP and ev.key == pygame.K_SPACE:
                if self.is_holding:
                    self.is_holding = False
                    self.hold_start_st = None
                    renpy.redraw(self, 0)

            if self.is_holding and self.hold_start_st is not None:
                if (st - self.hold_start_st) >= self.hold_duration:
                    self.is_holding = False
                    self.hold_start_st = None
                    # 补一句 redraw：像 Notify / Show 这类不会退场的 Action 会返回 None，
                    # 不提前重画的话，绿条会卡在满格消不掉
                    renpy.redraw(self, 0)
                    if self.action is not None:
                        return renpy.run(self.action)
                    return True
            return None

        def render(self, width, height, st, at):
            rv = renpy.Render(200, 20)
            rv.blit(renpy.render(Solid("#333333"), 200, 20, st, at), (0, 0))

            if self.is_holding and self.hold_start_st is not None:
                elapsed = st - self.hold_start_st
                progress = min(1.0, elapsed / self.hold_duration)
                bar_width = int(200 * progress)
                if bar_width > 0:
                    bar = renpy.render(Solid("#2ecc71"), bar_width, 20, st, at)
                    rv.blit(bar, (0, 0))
                renpy.timeout(0.01)
                renpy.redraw(self, 0)
            return rv


# --- 简单实例化出来给游戏画面看效果 ---

screen test_custom_box():
    add CustomBox(200, 200, color="#3498db") align (0.5, 0.45)

screen test_hold_advance():
    add _SpaceHoldAdvance(hold_duration=1.0) align (0.5, 0.45)

screen test_hold_notify():
    add SpaceHoldButton(hold_duration=1.0, action=Notify("触发 Notify 成功！")) align (0.5, 0.45)

screen test_hold_jump():
    add SpaceHoldButton(hold_duration=1.0, action=Jump("done_label")) align (0.5, 0.45)


label start:
    show screen test_custom_box
    "1. CustomBox：最简单的纯色方块，用来看 Render / render() / blit / visit。"
    hide screen test_custom_box

    show screen test_hold_advance
    "2. _SpaceHoldAdvance：现在按住空格 1 秒试试，满格后 return True 会直接过到下一句。"
    hide screen test_hold_advance

    show screen test_hold_notify
    "3. SpaceHoldButton（Notify）：按住空格 1 秒看左上角弹窗。因为补了 redraw，绿条会自动归零。点鼠标继续。"
    hide screen test_hold_notify

    show screen test_hold_jump
    "4. SpaceHoldButton（Jump）：最后再按住空格 1 秒，触发 Jump 跳转到结束标签。"
    hide screen test_hold_jump
    return


label done_label:
    hide screen test_hold_jump
    "已经成功用 SpaceHoldButton 跳到 done_label 啦，演示结束~"
    return
