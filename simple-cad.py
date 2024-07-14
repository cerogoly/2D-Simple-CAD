import wx
import wx.lib.colourdb
import matplotlib.colors as mcolors

###############################################################################
class DrawableElement:
    def __init__(self, element_type):
        self.element_name = ""
        self.element_type = element_type
        self.offset = [0, 0]
        self.isHighlighted = False

###############################################################################
class ImageElement(DrawableElement):
    def __init__(self, path, bitmap, position, scale=1.0, rotation=0):
        super().__init__('image')
        self.path = path
        self.bitmap = bitmap
        self.position = position
        self.scale = scale
        self.rotation = rotation

###############################################################################
class LineElement(DrawableElement):
    def __init__(self, start, end, width=1, color='black'):
        super().__init__('line')
        self.start = start
        self.end = end
        self.width = width
        self.color = color

###############################################################################
class ImageFrame(wx.Frame):

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self, *args, **kw):
        super(ImageFrame, self).__init__(*args, **kw)

        self.elements = []
        self.selected_element_index = -1
        self.drawing_line = False
        self.line_start = None
        self.dragging = False
        self.drag_offset = (0, 0)

        self.InitUI()

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def InitUI(self):
        self.splitter = wx.SplitterWindow(self)
        self.left_panel = wx.Panel(self.splitter, style=wx.BORDER_SUNKEN)
        self.right_panel = wx.Panel(self.splitter)

        self.splitter.SplitVertically(self.left_panel, self.right_panel, 200)

        self.vbox_left = wx.BoxSizer(wx.VERTICAL)
        self.filename_label = wx.StaticText(self.left_panel, label="Filename: ")
        self.vbox_left.Add(self.filename_label, flag=wx.ALL, border=5)
        
        self.x_label = wx.StaticText(self.left_panel, label="X: ")
        self.vbox_left.Add(self.x_label, flag=wx.ALL, border=5)
        
        self.y_label = wx.StaticText(self.left_panel, label="Y: ")
        self.vbox_left.Add(self.y_label, flag=wx.ALL, border=5)

        self.scale_label = wx.StaticText(self.left_panel, label="Scale: ")
        self.vbox_left.Add(self.scale_label, flag=wx.ALL, border=5)
        self.scale_input = wx.TextCtrl(self.left_panel, style=wx.TE_PROCESS_ENTER)
        self.vbox_left.Add(self.scale_input, flag=wx.ALL, border=5)
        self.scale_input.Bind(wx.EVT_TEXT_ENTER, self.OnScaleChanged)

        self.rotation_label = wx.StaticText(self.left_panel, label="Rotation: ")
        self.vbox_left.Add(self.rotation_label, flag=wx.ALL, border=5)
        self.rotation_input = wx.TextCtrl(self.left_panel, style=wx.TE_PROCESS_ENTER)
        self.vbox_left.Add(self.rotation_input, flag=wx.ALL, border=5)
        self.rotation_input.Bind(wx.EVT_TEXT_ENTER, self.OnRotationChanged)

        self.start_label = wx.StaticText(self.left_panel, label="Start: ")
        self.vbox_left.Add(self.start_label, flag=wx.ALL, border=5)

        self.end_label = wx.StaticText(self.left_panel, label="End: ")
        self.vbox_left.Add(self.end_label, flag=wx.ALL, border=5)

        self.line_width_label = wx.StaticText(self.left_panel, label="Line Width: ")
        self.vbox_left.Add(self.line_width_label, flag=wx.ALL, border=5)
        self.line_width_input = wx.TextCtrl(self.left_panel, style=wx.TE_PROCESS_ENTER)
        self.vbox_left.Add(self.line_width_input, flag=wx.ALL, border=5)
        self.line_width_input.Bind(wx.EVT_TEXT_ENTER, self.OnLineWidthChanged)

        self.line_color_label = wx.StaticText(self.left_panel, label="Line Color: ")
        self.vbox_left.Add(self.line_color_label, flag=wx.ALL, border=5)
        self.line_color_input = wx.TextCtrl(self.left_panel, style=wx.TE_PROCESS_ENTER)
        self.vbox_left.Add(self.line_color_input, flag=wx.ALL, border=5)
        self.line_color_input.Bind(wx.EVT_TEXT_ENTER, self.OnLineColorChanged)

        # Add navigation buttons for precise element positioning
        self.hbox_nav = wx.BoxSizer(wx.HORIZONTAL)
        self.vbox_left.Add(self.hbox_nav, flag=wx.ALIGN_CENTER | wx.ALL, border=5)

        up_btn    = wx.Button(self.left_panel, label="↑", size=(25, 25))
        down_btn  = wx.Button(self.left_panel, label="↓", size=(25, 25))
        left_btn  = wx.Button(self.left_panel, label="←", size=(25, 25))
        right_btn = wx.Button(self.left_panel, label="→", size=(25, 25))

        nav_grid = wx.GridSizer(3, 3, 0, 0)
        nav_grid.Add((0, 0), 0, wx.EXPAND)  # Empty space
        nav_grid.Add(up_btn, 0, wx.ALIGN_CENTER)
        nav_grid.Add((0, 0), 0, wx.EXPAND)  # Empty space
        nav_grid.Add(left_btn, 0, wx.ALIGN_CENTER)
        nav_grid.Add((0, 0), 0, wx.EXPAND)  # Empty space
        nav_grid.Add(right_btn, 0, wx.ALIGN_CENTER)
        nav_grid.Add((0, 0), 0, wx.EXPAND)  # Empty space
        nav_grid.Add(down_btn, 0, wx.ALIGN_CENTER)
        nav_grid.Add((0, 0), 0, wx.EXPAND)  # Empty space

        self.hbox_nav.Add(nav_grid, 0, wx.ALIGN_CENTER)

        # Bind button events
        up_btn.Bind(wx.EVT_BUTTON, self.OnMoveUp)
        down_btn.Bind(wx.EVT_BUTTON, self.OnMoveDown)
        left_btn.Bind(wx.EVT_BUTTON, self.OnMoveLeft)
        right_btn.Bind(wx.EVT_BUTTON, self.OnMoveRight)

        self.left_panel.SetSizer(self.vbox_left)

        self.toolbar = self.CreateToolBar()
        open_tool      = self.toolbar.AddTool(wx.ID_OPEN, 'Open', wx.Bitmap('load_icon.png'))
        draw_line_tool = self.toolbar.AddTool(wx.ID_ANY,  'Draw Line', wx.Bitmap('line_icon.png'))
        exit_tool      = self.toolbar.AddTool(wx.ID_EXIT, 'Exit', wx.Bitmap('exit_icon.png'))
        self.toolbar.Realize()

        self.Bind(wx.EVT_TOOL, self.OnOpen, open_tool)
        self.Bind(wx.EVT_TOOL, self.OnDrawLine, draw_line_tool)
        self.Bind(wx.EVT_TOOL, self.OnExit, exit_tool)

        self.right_panel.Bind(wx.EVT_PAINT, self.OnPaint)
        self.right_panel.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.right_panel.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self.right_panel.Bind(wx.EVT_MOTION, self.OnMotion)
        self.Bind(wx.EVT_CHAR_HOOK, self.OnKeyDown)

        self.grid_spacing = 10
        self.right_panel.Bind(wx.EVT_MOUSE_CAPTURE_LOST, self.OnMouseCaptureLost)
    
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def OnMoveUp(self, event):
        if self.selected_element_index != -1:
            self.MoveElement(0, -1)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def OnMoveDown(self, event):
        if self.selected_element_index != -1:
            self.MoveElement(0, 1)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def OnMoveLeft(self, event):
        if self.selected_element_index != -1:
            self.MoveElement(-1, 0)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def OnMoveRight(self, event):
        if self.selected_element_index != -1:
            self.MoveElement(1, 0)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def MoveElement(self, dx, dy):
        element = self.elements[self.selected_element_index]
        element.offset[0] += dx
        element.offset[1] += dy
        self.Refresh()

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def OnExit(self, event):
        self.Close()

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def OnOpen(self, event):
        with wx.FileDialog(self, "Open Image file", wildcard="Image files (*.png;*.jpg;*.bmp)|*.png;*.jpg;*.bmp",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return

            pathname = fileDialog.GetPath()
            img = wx.Image(pathname, wx.BITMAP_TYPE_ANY)
            img = img.Scale(img.GetWidth(), img.GetHeight())
            bmp = wx.Bitmap(img)
            position = self.SnapToGrid(50, 50)
            self.elements.append(ImageElement(path=pathname, bitmap=bmp, position=position))
            self.right_panel.Refresh()

    def OnDrawLine(self, event):
        self.drawing_line = True

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def OnPaint(self, event):
        dc = wx.BufferedPaintDC(self.right_panel)
        dc.Clear()
        self.DrawGrid(dc)
        
        for element in self.elements:
            if element.element_type == 'image':
                self.DrawImage(dc, element)
            elif element.element_type == 'line':
                self.DrawLine(dc, element)
                
        if self.selected_element_index != -1:
            self.HighlightSelectedElement(dc)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def DrawGrid(self, dc):
        dc.SetPen(wx.Pen(wx.BLACK, 1))
        width, height = self.right_panel.GetSize()
        for x in range(0, width, self.grid_spacing):
            for y in range(0, height, self.grid_spacing):
                dc.DrawPoint(x, y)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def DrawImage(self, dc, image):
        ox, oy = image.offset
        bitmap = self.TransformImage(image)
        dc.DrawBitmap(bitmap, image.position[0]+ox, image.position[1]+oy, True)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def DrawLine(self, dc, line):
        dc.SetPen(wx.Pen(wx.Colour(line.color), line.width))
        ox, oy = line.offset
        dc.DrawLine(line.start[0]+ox, line.start[1]+oy, 
                    line.end[0]  +ox, line.end[1]  +oy)
        self.DrawLineEndSquares(dc, line)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def HighlightSelectedElement(self, dc):
        element = self.elements[self.selected_element_index]
        ox, oy = element.offset
        if element.element_type == 'image':
            bitmap = self.TransformImage(element)
            dc.SetPen(wx.Pen(wx.Colour(128, 128, 128), 1, wx.PENSTYLE_DOT))
            dc.SetBrush(wx.TRANSPARENT_BRUSH)
            dc.DrawRectangle(element.position[0]+ox, element.position[1]+oy, 
                             bitmap.GetWidth(), bitmap.GetHeight())
        elif element.element_type == 'line':
            dc.SetPen(wx.Pen(wx.Colour(128, 128, 128), 1, wx.PENSTYLE_DOT))
            dc.SetBrush(wx.TRANSPARENT_BRUSH)
            dc.DrawLine(element.start[0]+ox, element.start[1]+oy, 
                        element.end[0]  +ox, element.end[1]  +oy)
            self.DrawLineEndSquares(dc, element)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def SnapToGrid(self, x, y):
        new_x = round(x / self.grid_spacing) * self.grid_spacing
        new_y = round(y / self.grid_spacing) * self.grid_spacing
        return new_x, new_y

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def OnLeftDown(self, event):
        x, y = self.SnapToGrid(event.GetPosition()[0], event.GetPosition()[1])
        self.SelectElement(x, y)
        
        if self.selected_element_index != -1:
            element = self.elements[self.selected_element_index]
            if element.element_type == 'image':
                self.dragging = True
                self.drag_offset = (x - element.position[0], y - element.position[1])
                self.right_panel.CaptureMouse()
        elif self.drawing_line:
            self.line_start = (x, y)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def OnLeftUp(self, event):
        if self.drawing_line and self.line_start:
            x, y = self.SnapToGrid(event.GetPosition()[0], event.GetPosition()[1])
            new_line = LineElement(start=self.line_start, end=(x, y))
            self.elements.append(new_line)
            self.line_start = None
            self.drawing_line = False
            self.right_panel.Refresh()

        if self.dragging:
            self.dragging = False
            if self.right_panel.HasCapture():
                self.right_panel.ReleaseMouse()

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def OnMotion(self, event):
        if self.dragging and self.selected_element_index != -1 and event.Dragging() and event.LeftIsDown():
            x, y = self.SnapToGrid(event.GetPosition()[0], event.GetPosition()[1])
            element = self.elements[self.selected_element_index]
            ox, oy = element.offset
            if element.element_type == 'image':
                element.position = (x - self.drag_offset[0] + ox, y - self.drag_offset[1] + oy)
                self.UpdateLabels(element)
                self.right_panel.Refresh()

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def OnKeyDown(self, event):
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_DELETE:
            if self.selected_element_index != -1:
                del self.elements[self.selected_element_index]
                self.selected_element_index = -1
                self.right_panel.Refresh()
        event.Skip()

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def TransformImage(self, image):
        img = wx.Image(image.path, wx.BITMAP_TYPE_ANY)
        img = img.Scale(int(img.GetWidth() * image.scale), int(img.GetHeight() * image.scale))

        if image.rotation != 0:
            img = img.Rotate(image.rotation * (3.14 / 180), (img.GetWidth() / 2, img.GetHeight() / 2))

        return wx.Bitmap(img)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def SelectElement(self, x, y):
        self.selected_element_index = -1
        for i, element in enumerate(self.elements):
            if element.element_type == 'image':
                bitmap = self.TransformImage(element)
                img_rect = wx.Rect(element.position[0], element.position[1], bitmap.GetWidth(), bitmap.GetHeight())
                if img_rect.Contains(x, y):
                    self.selected_element_index = i
                    self.UpdateLabels(element)
                    break
            elif element.element_type == 'line':
                buffer = 5  # Buffer distance for easier selection
                if ((element.start[0] - buffer <= x <= element.end[0] + buffer and 
                     element.start[1] - buffer <= y <= element.end[1] + buffer) or
                    (element.end[0] - buffer <= x <= element.start[0] + buffer and 
                     element.end[1] - buffer <= y <= element.start[1] + buffer)):
                    self.selected_element_index = i
                    self.UpdateLabels(element)
                    break

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def UpdateLabels(self, element):
        if element.element_type == 'image':
            self.filename_label.SetLabel(f"Filename: {element.path}")
            self.x_label.SetLabel(f"X: {element.position[0]}")
            self.y_label.SetLabel(f"Y: {element.position[1]}")
            self.scale_label.SetLabel(f"Scale: {element.scale}")
            self.rotation_label.SetLabel(f"Rotation: {element.rotation}")
            self.start_label.SetLabel(f"Start: N/A")
            self.end_label.SetLabel(f"End: N/A")
            self.line_width_label.SetLabel(f"Line Width: N/A")
            self.line_color_label.SetLabel(f"Line Color: N/A")
        elif element.element_type == 'line':
            self.filename_label.SetLabel(f"Filename: N/A")
            self.x_label.SetLabel(f"X: N/A")
            self.y_label.SetLabel(f"Y: N/A")
            self.scale_label.SetLabel(f"Scale: N/A")
            self.rotation_label.SetLabel(f"Rotation: N/A")
            self.start_label.SetLabel(f"Start: {element.start}")
            self.end_label.SetLabel(f"End: {element.end}")
            self.line_width_label.SetLabel(f"Line Width: {element.width}")
            self.line_color_label.SetLabel(f"Line Color: {element.color}")

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def OnScaleChanged(self, event):
        if self.selected_element_index != -1:
            element = self.elements[self.selected_element_index]
            if element.element_type == 'image':
                try:
                    new_scale = float(self.scale_input.GetValue())
                    element.scale = new_scale
                    self.UpdateLabels(element)
                    self.right_panel.Refresh()
                except ValueError:
                    pass

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def OnRotationChanged(self, event):
        if self.selected_element_index != -1:
            element = self.elements[self.selected_element_index]
            if element.element_type == 'image':
                try:
                    new_rotation = float(self.rotation_input.GetValue())
                    element.rotation = new_rotation
                    self.UpdateLabels(element)
                    self.right_panel.Refresh()
                except ValueError:
                    pass

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def OnLineWidthChanged(self, event):
        if self.selected_element_index != -1:
            element = self.elements[self.selected_element_index]
            if element.element_type == 'line':
                try:
                    new_width = int(self.line_width_input.GetValue())
                    element.width = new_width
                    self.UpdateLabels(element)
                    self.right_panel.Refresh()
                except ValueError:
                    pass
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def OnLineColorChanged(self, event):
        if self.selected_element_index != -1:
            element = self.elements[self.selected_element_index]
            if element.element_type == 'line':
                new_color = self.line_color_input.GetValue()
                if new_color in mcolors.CSS4_COLORS:
                    element.color = new_color
                    self.UpdateLabels(element)
                    self.right_panel.Refresh()

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def DrawLineEndSquares(self, dc, line):
        square_size = 4
        ox, oy = line.offset
        for point in [line.start, line.end]:
            dc.SetBrush(wx.Brush(wx.BLACK))
            dc.DrawRectangle(point[0] - square_size // 2 + ox, 
                             point[1] - square_size // 2 + oy, 
                             square_size, square_size)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def OnMouseCaptureLost(self, event):
        self.dragging = False

##############################################################################
def main():
    app = wx.App(False)
    frame = ImageFrame(None, title='Image Drawer', size=(800, 600))
    frame.Show()
    app.MainLoop()

if __name__ == '__main__':
    main()
