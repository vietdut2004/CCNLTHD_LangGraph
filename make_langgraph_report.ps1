param(
    [string]$OutDir = ".\generated_langgraph_assets"
)

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
Add-Type -AssemblyName System.Drawing

function New-Diagram {
    param(
        [string]$Path,
        [string]$Title,
        [string]$Subtitle,
        [string[]]$Nodes,
        [string[]]$Footer = @()
    )

    $w = 1400
    $h = 820
    $bmp = New-Object System.Drawing.Bitmap $w, $h
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::ClearTypeGridFit

    $bg = [System.Drawing.Color]::FromArgb(246, 248, 252)
    $ink = [System.Drawing.Color]::FromArgb(31, 41, 55)
    $muted = [System.Drawing.Color]::FromArgb(86, 99, 118)
    $colors = @(
        [System.Drawing.Color]::FromArgb(37, 99, 235),
        [System.Drawing.Color]::FromArgb(22, 163, 74),
        [System.Drawing.Color]::FromArgb(217, 119, 6),
        [System.Drawing.Color]::FromArgb(124, 58, 237),
        [System.Drawing.Color]::FromArgb(14, 165, 233),
        [System.Drawing.Color]::FromArgb(220, 38, 38)
    )
    $line = [System.Drawing.Color]::FromArgb(148, 163, 184)
    $white = [System.Drawing.Color]::White

    $g.Clear($bg)
    $titleFont = New-Object System.Drawing.Font("Segoe UI", 42, [System.Drawing.FontStyle]::Bold)
    $subFont = New-Object System.Drawing.Font("Segoe UI", 21, [System.Drawing.FontStyle]::Regular)
    $nodeFont = New-Object System.Drawing.Font("Segoe UI", 22, [System.Drawing.FontStyle]::Bold)
    $smallFont = New-Object System.Drawing.Font("Segoe UI", 17, [System.Drawing.FontStyle]::Regular)

    $g.DrawString($Title, $titleFont, (New-Object System.Drawing.SolidBrush($ink)), 70, 55)
    $g.DrawString($Subtitle, $subFont, (New-Object System.Drawing.SolidBrush($muted)), 74, 120)

    $cols = [Math]::Min(3, [Math]::Max(1, $Nodes.Count))
    $boxW = 360
    $boxH = 118
    $gapX = 80
    $gapY = 92
    $startX = [int](($w - ($cols * $boxW + ($cols - 1) * $gapX)) / 2)
    $startY = 230

    $points = @()
    for ($i = 0; $i -lt $Nodes.Count; $i++) {
        $row = [Math]::Floor($i / $cols)
        $col = $i % $cols
        $x = $startX + $col * ($boxW + $gapX)
        $y = $startY + $row * ($boxH + $gapY)
        $points += ,@($x, $y)
    }

    $arrowPen = New-Object System.Drawing.Pen($line, 5)
    $arrowPen.EndCap = [System.Drawing.Drawing2D.LineCap]::ArrowAnchor
    for ($i = 0; $i -lt $points.Count - 1; $i++) {
        $x1 = $points[$i][0] + $boxW
        $y1 = $points[$i][1] + ($boxH / 2)
        $x2 = $points[$i + 1][0]
        $y2 = $points[$i + 1][1] + ($boxH / 2)
        if ($points[$i][1] -ne $points[$i + 1][1]) {
            $x1 = $points[$i][0] + ($boxW / 2)
            $y1 = $points[$i][1] + $boxH
            $x2 = $points[$i + 1][0] + ($boxW / 2)
            $y2 = $points[$i + 1][1]
        }
        $g.DrawLine($arrowPen, [int]$x1, [int]$y1, [int]$x2, [int]$y2)
    }

    for ($i = 0; $i -lt $Nodes.Count; $i++) {
        $x = $points[$i][0]
        $y = $points[$i][1]
        $rect = New-Object System.Drawing.RectangleF([float]$x, [float]$y, [float]$boxW, [float]$boxH)
        $shape = New-Object System.Drawing.Drawing2D.GraphicsPath
        $radius = 18
        $shape.AddArc($x, $y, $radius, $radius, 180, 90)
        $shape.AddArc($x + $boxW - $radius, $y, $radius, $radius, 270, 90)
        $shape.AddArc($x + $boxW - $radius, $y + $boxH - $radius, $radius, $radius, 0, 90)
        $shape.AddArc($x, $y + $boxH - $radius, $radius, $radius, 90, 90)
        $shape.CloseFigure()
        $g.FillPath((New-Object System.Drawing.SolidBrush($white)), $shape)
        $g.DrawPath((New-Object System.Drawing.Pen($colors[$i % $colors.Count], 5)), $shape)
        $sf = New-Object System.Drawing.StringFormat
        $sf.Alignment = [System.Drawing.StringAlignment]::Center
        $sf.LineAlignment = [System.Drawing.StringAlignment]::Center
        $g.DrawString($Nodes[$i], $nodeFont, (New-Object System.Drawing.SolidBrush($ink)), $rect, $sf)
        $shape.Dispose()
    }

    $fy = 700
    foreach ($lineText in $Footer) {
        $g.DrawString($lineText, $smallFont, (New-Object System.Drawing.SolidBrush($muted)), 78, $fy)
        $fy += 32
    }

    $bmp.Save($Path, [System.Drawing.Imaging.ImageFormat]::Png)
    $g.Dispose()
    $bmp.Dispose()
}

New-Diagram "$OutDir\overview.png" "LangGraph" "Framework for stateful AI workflows as graphs" @("State", "Node", "Edge", "Conditional Routing", "Tool", "Checkpoint") @("Best for multi-step chatbots, agent control flow, and RAG pipelines.")
New-Diagram "$OutDir\install.png" "Install LangGraph" "Python environment for stateful AI apps" @("python -m venv .venv", "pip install langgraph", "pip install langchain-openai", "Run graph") @("LangGraph can work with langchain-openai and langchain-core integrations.")
New-Diagram "$OutDir\stategraph.png" "StateGraph Chatbot" "Conversation flow with state, nodes, and conditional edges" @("User input", "Update state", "LLM node", "Tool node", "Route", "Response") @("State is passed through nodes so the system keeps context and chooses the next step.")
New-Diagram "$OutDir\rag.png" "RAG with LangGraph" "Retrieval, generation, and validation are separate nodes" @("Question", "Retrieve docs", "Grade context", "Generate answer", "Validate", "Final") @("Graph design makes query rewrite, fallback search, and review steps easier to add.")
New-Diagram "$OutDir\agent.png" "Agent Workflow" "Tool use is controlled by graph routing" @("Planner", "Select tool", "Execute tool", "Observe", "Decide", "Answer") @("Agent loops are easier to control with stop conditions and checkpoints.")
New-Diagram "$OutDir\api.png" "API Deployment" "FastAPI connects the graph, model, and external tools" @("Client", "FastAPI", "Compiled graph", "LLM", "Tools", "LangSmith") @("LangSmith supports tracing, debugging, and graph evaluation.")
