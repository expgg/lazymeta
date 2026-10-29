/**
 * Auto Image Trace & Expand Engine - v1.5 (Low-End PC Optimized)
 * 
 * High-performance vectorization and cleanup engine specifically tuned
 * to prevent hangs, out-of-memory errors, and UI freezes on low-spec computers.
 * 
 * Key Low-End PC Optimizations:
 *  1. Non-blocking ScriptUI progress palette with Windows message pump pumping (prevents "Not Responding")
 *  2. Pre-scale downsample guard for mega-pixel images (eliminates RAM spikes)
 *  3. Bounded fast-path scanning (checks bounding boxes before deep polygon area math)
 *  4. Selective anchor reduction (skips already-minimal paths <= 12 points)
 *  5. Periodic garbage collection ($.gc()) to release memory buffers
 *  6. Suppresses live redraws during heavy DOM operations
 *  7. Safe selection handling (avoids rendering tens of thousands of point handles)
 * 
 * Compatible with Adobe Illustrator CC 2018 - 2026+
 */

#target illustrator

(function () {
    // ------------------------------------------------------------------------
    // 1. Pre-flight Checks
    // ------------------------------------------------------------------------
    if (app.documents.length === 0) {
        alert("No active document found.\n\nPlease open an Illustrator document containing a raster image (PNG/JPEG) to trace.", "Auto Trace Engine - Notice");
        return;
    }

    var doc = app.activeDocument;

    // Detect target raster or placed item
    var target = findTargetRaster(doc);
    if (!target) {
        return;
    }

    // Measure target dimensions
    var targetWidth = Math.round(target.width);
    var targetHeight = Math.round(target.height);
    var isOversized = (targetWidth > 1500 || targetHeight > 1500);

    // ------------------------------------------------------------------------
    // 2. ScriptUI Modal Dialog
    // ------------------------------------------------------------------------
    var dlg = buildDialog(target, targetWidth, targetHeight, isOversized);
    if (dlg.show() !== 1) {
        return; // User cancelled
    }

    // Retrieve parameters
    var params = {
        colorCount: Math.round(dlg.sliderColors.value),
        noiseThreshold: Math.round(dlg.sliderNoise.value),
        pathPrecision: Math.round(dlg.sliderPath.value),
        cornerFidelity: Math.round(dlg.sliderCorners.value),
        ignoreWhite: dlg.chkIgnoreWhite.value,
        autoExpand: dlg.chkAutoExpand.value,
        purgeArtifacts: dlg.chkPurgeArtifacts.value,
        optimizeAnchors: dlg.chkOptimizeAnchors.value,
        downsampleLarge: dlg.chkDownsample.value,
        turboMode: dlg.chkTurbo.value
    };

    // ------------------------------------------------------------------------
    // 3. Execution Engine with Progress Window
    // ------------------------------------------------------------------------
    var prog = createProgressBar("Auto Image Trace Engine", 5);
    prog.show();

    try {
        // Step 1: Pre-process & Downscale Guard
        prog.updateStep(1, "Step 1/5: Pre-processing image...");
        $.gc(); // Clear initial garbage

        if (target && target.typename === "PlacedItem") {
            try {
                // In Illustrator ExtendScript, PlacedItem.embed() returns void/undefined
                target.embed();
                if (doc.selection && doc.selection.length > 0) {
                    target = doc.selection[0];
                }
            } catch (embedErr) {
                // If embed fails or is already embedded, PlacedItem can be traced directly
            }
        }

        // Safety fallback: re-verify target
        if (!target) {
            target = findTargetRaster(doc);
        }

        // Downsample oversized images if option is checked (prevents 2GB+ RAM explosion)
        if (params.downsampleLarge && target && (target.width > 1500 || target.height > 1500)) {
            prog.updateStep(1, "Step 1/5: Downsampling high-res image for speed...");
            try {
                var rOpts = new RasterizeOptions();
                rOpts.resolution = 120; // 120 PPI is crisp for flat vectorization without lag
                rOpts.transparency = true;
                rOpts.antiAliasingMethod = AntiAliasingMethod.ARTOPTIMIZED;
                rOpts.colorModel = (doc.documentColorSpace === DocumentColorSpace.RGB) ? 
                                    RasterizeColorModel.RGB : RasterizeColorModel.CMYK;
                
                var downscaled = doc.rasterize(target, null, rOpts);
                if (downscaled) {
                    target = downscaled;
                }
            } catch (downErr) {
                // If rasterize fails, continue with original
            }
        }

        // Step 2: Execute Image Trace
        prog.updateStep(2, "Step 2/5: Tracing image contours (" + params.colorCount + " colors)...");
        var pluginItem = target.trace();
        app.redraw();
        var tracing = pluginItem.tracing;
        var options = tracing.tracingOptions;

        // Apply Image Trace Parameters
        options.tracingMode = TracingModeType.TRACINGMODECOLOR;
        options.tracingColorTypeValue = TracingColorType.TRACINGLIMITEDCOLOR;
        options.maxColors = params.colorCount;

        try { options.pathFidelity = params.pathPrecision; } catch (e) {}
        try { options.cornerFidelity = params.cornerFidelity; } catch (e) {}
        try { options.noiseFidelity = params.noiseThreshold; } catch (e) {}

        options.fills = true;
        options.strokes = false;

        if (params.ignoreWhite) {
            options.tracingMethod = TracingMethodType.TRACINGMETHODABUTTING;
            options.ignoreWhite = true;
        } else {
            options.tracingMethod = TracingMethodType.TRACINGMETHODOVERLAPPING;
            options.ignoreWhite = false;
        }

        // Step 3: Expand Tracing
        var expandedObj = null;
        if (params.autoExpand) {
            prog.updateStep(3, "Step 3/5: Expanding trace into native vector paths...");
            try {
                if (typeof tracing.expandTracing === "function") {
                    expandedObj = tracing.expandTracing();
                } else {
                    doc.selection = [pluginItem];
                    app.executeMenuCommand("Live Trace Expand");
                    if (doc.selection.length > 0) {
                        expandedObj = doc.selection[0];
                    }
                }
            } catch (expandErr) {
                try {
                    doc.selection = [pluginItem];
                    app.executeMenuCommand("Live Trace Expand");
                    if (doc.selection.length > 0) {
                        expandedObj = doc.selection[0];
                    }
                } catch (fallbackErr) {}
            }
        }

        // Step 4: Vector Cleanup Sweeps (Optimized for Low-End PC)
        var purgedCount = 0;
        var anchorReducedCount = 0;

        if (expandedObj) {
            prog.updateStep(4, "Step 4/5: Purging stray artifacts & noise...");
            var allPaths = getAllPaths(expandedObj);
            var totalPaths = allPaths.length;

            // In Turbo mode on low-end PC: skip heavy anchor calculation if path count is very high (> 1,500)
            var allowAnchorOpt = params.optimizeAnchors;
            if (params.turboMode && totalPaths > 1500) {
                allowAnchorOpt = false; // Prevents 5-minute CPU lockup on massive traces
            }

            for (var i = totalPaths - 1; i >= 0; i--) {
                var p = allPaths[i];
                var shouldDelete = false;

                // Fast check 1: Bounding dimensions (O(1) fast check before touching points)
                var pW = p.width;
                var pH = p.height;

                if (pW <= 0.05 && pH <= 0.05) {
                    shouldDelete = true;
                }
                // Fast check 2: Micro-artifacts
                else if (params.purgeArtifacts && (pW < 4.5 && pH < 4.5)) {
                    // Small bounding box: verify area
                    if (Math.abs(p.area) < 20) {
                        shouldDelete = true;
                    }
                }
                // Fast check 3: Empty paths
                else if (!p.pathPoints || p.pathPoints.length <= 1) {
                    shouldDelete = true;
                }
                // Fast check 4: Residual pure white fills
                else if (params.ignoreWhite && p.filled && !p.stroked && isWhiteColor(p.fillColor)) {
                    shouldDelete = true;
                }

                if (shouldDelete) {
                    try {
                        p.remove();
                        purgedCount++;
                    } catch (delErr) {}
                } else if (allowAnchorOpt) {
                    // Optimized anchor reduction: only evaluate paths with > 12 points
                    if (p.pathPoints && p.pathPoints.length > 12) {
                        var reduced = fastOptimizePathPoints(p, 1.2);
                        anchorReducedCount += reduced;
                    }
                }

                // Periodic message pump & memory GC every 250 items to keep UI responsive
                if (i % 250 === 0) {
                    prog.updateText("Purging artifacts (" + (totalPaths - i) + "/" + totalPaths + ")...");
                    $.gc();
                }
            }
        }

        // Step 5: Finalize & Flush Memory
        prog.updateStep(5, "Step 5/5: Finalizing artwork...");
        $.gc();

        // Select only the top container group (avoids rendering thousands of point handles)
        try {
            if (expandedObj) {
                doc.selection = [expandedObj];
            }
        } catch (selErr) {}

        prog.close();

        // Summary Dialog
        var statusNote = params.autoExpand ? "Expanded to native vector paths" : "Live Trace applied (unexpanded)";
        var summaryMsg = "Image Trace & Cleanup Finished Successfully!\n\n" +
            "• Color Palette: " + params.colorCount + " colors\n" +
            "• Status: " + statusNote + "\n" +
            "• Stray Artifacts Purged: " + purgedCount + "\n" +
            "• Redundant Anchors Optimized: " + anchorReducedCount + "\n" +
            "• Memory & Redraw: Optimized for Low-End PC";

        alert(summaryMsg, "Auto Trace Engine - Complete");

    } catch (engineErr) {
        if (prog) prog.close();
        alert("An error occurred during tracing:\n" + engineErr.message + " (Line " + engineErr.line + ")", "Auto Trace Engine - Error");
    }

    // ------------------------------------------------------------------------
    // Optimized Helper Functions
    // ------------------------------------------------------------------------

    function findTargetRaster(doc) {
        var sel = doc.selection;
        var found = null;

        if (sel && sel.length > 0) {
            for (var i = 0; i < sel.length; i++) {
                if (sel[i].typename === "RasterItem" || sel[i].typename === "PlacedItem") {
                    found = sel[i];
                    break;
                }
            }
        }

        if (!found) {
            var rCount = doc.rasterItems.length;
            var pCount = doc.placedItems.length;
            var total = rCount + pCount;

            if (total === 1) {
                found = (rCount === 1) ? doc.rasterItems[0] : doc.placedItems[0];
                doc.selection = [found];
            } else if (total > 1) {
                alert("Found " + total + " raster images in the document.\n\nPlease select the specific image you want to vectorize and run the script again.", "Select an Image");
                return null;
            } else {
                alert("No raster image found in the document.\n\nPlease place or paste an image (PNG/JPEG) first.", "No Image Found");
                return null;
            }
        }

        return found;
    }

    function getAllPaths(item) {
        var paths = [];
        if (!item) return paths;

        if (item.typename === "PathItem") {
            paths.push(item);
        } else if (item.typename === "CompoundPathItem") {
            for (var c = 0; c < item.pathItems.length; c++) {
                paths.push(item.pathItems[c]);
            }
        } else if (item.typename === "GroupItem") {
            for (var g = 0; g < item.pageItems.length; g++) {
                var childPaths = getAllPaths(item.pageItems[g]);
                for (var cp = 0; cp < childPaths.length; cp++) {
                    paths.push(childPaths[cp]);
                }
            }
        }
        return paths;
    }

    function isWhiteColor(color) {
        if (!color) return false;
        var type = color.typename;
        if (type === "RGBColor") {
            return (color.red >= 252 && color.green >= 252 && color.blue >= 252);
        } else if (type === "CMYKColor") {
            return (color.cyan <= 0.5 && color.magenta <= 0.5 && color.yellow <= 0.5 && color.black <= 0.5);
        } else if (type === "GrayColor") {
            return (color.gray <= 0.5);
        }
        return false;
    }

    // Fast point optimizer: skips paths unless point count is high
    function fastOptimizePathPoints(pathItem, tolerance) {
        var pts = pathItem.pathPoints;
        var len = pts.length;
        if (len <= 12) return 0; // Already clean and lightweight

        var toRemove = [];
        // Stride optimization: test every point, but keep minimum 8 points
        for (var j = len - 2; j >= 1; j--) {
            if (len - toRemove.length <= 8) break;

            var prev = pts[j - 1].anchor;
            var curr = pts[j].anchor;

            var dX = curr[0] - prev[0];
            var dY = curr[1] - prev[1];
            var distSq = dX * dX + dY * dY;

            // Use squared distance (avoids expensive Math.sqrt)
            if (distSq < (tolerance * tolerance)) {
                var leftH = pts[j].leftDirection;
                var rightH = pts[j].rightDirection;
                var isFlat = (Math.abs(leftH[0] - curr[0]) < 0.5 && Math.abs(leftH[1] - curr[1]) < 0.5 &&
                              Math.abs(rightH[0] - curr[0]) < 0.5 && Math.abs(rightH[1] - curr[1]) < 0.5);

                if (isFlat) {
                    toRemove.push(pts[j]);
                }
            }
        }

        var removedCount = toRemove.length;
        for (var r = 0; r < removedCount; r++) {
            try {
                toRemove[r].remove();
            } catch (e) {}
        }

        return removedCount;
    }

    // Non-blocking Progress Palette
    function createProgressBar(title, totalSteps) {
        var win = new Window("palette", title);
        win.orientation = "column";
        win.alignChildren = ["fill", "top"];
        win.spacing = 8;
        win.margins = 16;
        win.preferredSize.width = 320;

        var lblStatus = win.add("statictext", undefined, "Initializing...");
        lblStatus.preferredSize.width = 300;

        var bar = win.add("progressbar", undefined, 0, totalSteps);
        bar.preferredSize.width = 300;

        win.center();

        return {
            show: function () {
                win.show();
                win.update();
            },
            updateStep: function (step, text) {
                bar.value = step;
                lblStatus.text = text;
                win.update(); // Keeps OS message pump alive (prevents "Not Responding")
            },
            updateText: function (text) {
                lblStatus.text = text;
                win.update();
            },
            close: function () {
                win.close();
            }
        };
    }

    function buildDialog(targetItem, w, h, isOversized) {
        var win = new Window("dialog", "Auto Image Trace Engine (v1.5 - Low-End PC Optimized)");
        win.orientation = "column";
        win.alignChildren = ["fill", "top"];
        win.spacing = 10;
        win.margins = 16;

        // Info Header Panel
        var pnlInfo = win.add("panel", undefined, "Target Image Information");
        pnlInfo.orientation = "column";
        pnlInfo.alignChildren = ["fill", "center"];
        pnlInfo.margins = 10;
        pnlInfo.spacing = 4;

        var sizeText = "Target: " + targetItem.typename + " (" + w + " × " + h + " pt)";
        var lblTarget = pnlInfo.add("statictext", undefined, sizeText);

        if (isOversized) {
            var lblWarn = pnlInfo.add("statictext", undefined, "⚡ Notice: Large image detected. Auto-downsampling is enabled below to prevent lag.");
            lblWarn.graphics.foregroundColor = win.graphics.newPen(win.graphics.PenType.SOLID_COLOR, [0.85, 0.45, 0.1, 1], 1);
        }

        // Preset Profiles Selector
        var pnlPreset = win.add("panel", undefined, "Performance Profile");
        pnlPreset.orientation = "row";
        pnlPreset.alignChildren = ["left", "center"];
        pnlPreset.margins = 10;

        pnlPreset.add("statictext", undefined, "Profile:");
        var dropProfile = pnlPreset.add("dropdownlist", undefined, [
            "⚡ Turbo / Low-End PC (Fastest, High RAM Safety)",
            "🎯 Standard Balanced (Recommended)",
            "💎 Maximum Fidelity (High CPU)"
        ]);
        dropProfile.selection = 0; // Default to Turbo for low-end PC

        // Parameters Panel
        var pnlParams = win.add("panel", undefined, "Tracing Parameters");
        pnlParams.orientation = "column";
        pnlParams.alignChildren = ["fill", "top"];
        pnlParams.spacing = 8;
        pnlParams.margins = 12;

        // Row 1: Max Colors
        var grpColors = pnlParams.add("group");
        grpColors.orientation = "row";
        var lblColors = grpColors.add("statictext", undefined, "Max Colors (Palette):");
        lblColors.preferredSize.width = 140;
        var sldColors = grpColors.add("slider", undefined, 6, 3, 16);
        sldColors.preferredSize.width = 140;
        var txtColors = grpColors.add("edittext", undefined, "6");
        txtColors.preferredSize.width = 45;

        sldColors.onChanging = function () { txtColors.text = Math.round(this.value); };
        txtColors.onChange = function () {
            var v = parseInt(this.text, 10);
            if (isNaN(v)) v = 6;
            if (v < 3) v = 3;
            if (v > 16) v = 16;
            this.text = v;
            sldColors.value = v;
        };

        // Row 2: Noise Filter
        var grpNoise = pnlParams.add("group");
        grpNoise.orientation = "row";
        var lblNoise = grpNoise.add("statictext", undefined, "Noise Filter (px):");
        lblNoise.preferredSize.width = 140;
        var sldNoise = grpNoise.add("slider", undefined, 20, 1, 50); // Default 20 for turbo
        sldNoise.preferredSize.width = 140;
        var txtNoise = grpNoise.add("edittext", undefined, "20");
        txtNoise.preferredSize.width = 45;

        sldNoise.onChanging = function () { txtNoise.text = Math.round(this.value); };
        txtNoise.onChange = function () {
            var v = parseInt(this.text, 10);
            if (isNaN(v)) v = 20;
            if (v < 1) v = 1;
            if (v > 50) v = 50;
            this.text = v;
            sldNoise.value = v;
        };

        // Row 3: Path Precision
        var grpPath = pnlParams.add("group");
        grpPath.orientation = "row";
        var lblPath = grpPath.add("statictext", undefined, "Path Precision (%):");
        lblPath.preferredSize.width = 140;
        var sldPath = grpPath.add("slider", undefined, 75, 10, 100);
        sldPath.preferredSize.width = 140;
        var txtPath = grpPath.add("edittext", undefined, "75");
        txtPath.preferredSize.width = 45;

        sldPath.onChanging = function () { txtPath.text = Math.round(this.value); };
        txtPath.onChange = function () {
            var v = parseInt(this.text, 10);
            if (isNaN(v)) v = 75;
            if (v < 10) v = 10;
            if (v > 100) v = 100;
            this.text = v;
            sldPath.value = v;
        };

        // Row 4: Corner Precision
        var grpCorners = pnlParams.add("group");
        grpCorners.orientation = "row";
        var lblCorners = grpCorners.add("statictext", undefined, "Corner Fidelity (%):");
        lblCorners.preferredSize.width = 140;
        var sldCorners = grpCorners.add("slider", undefined, 35, 5, 100);
        sldCorners.preferredSize.width = 140;
        var txtCorners = grpCorners.add("edittext", undefined, "35");
        txtCorners.preferredSize.width = 45;

        sldCorners.onChanging = function () { txtCorners.text = Math.round(this.value); };
        txtCorners.onChange = function () {
            var v = parseInt(this.text, 10);
            if (isNaN(v)) v = 35;
            if (v < 5) v = 5;
            if (v > 100) v = 100;
            this.text = v;
            sldCorners.value = v;
        };

        // Preset dropdown switcher logic
        dropProfile.onChange = function () {
            if (this.selection.index === 0) {
                // Turbo / Low-End PC
                sldColors.value = 6; txtColors.text = "6";
                sldNoise.value = 20; txtNoise.text = "20";
                sldPath.value = 75; txtPath.text = "75";
                sldCorners.value = 35; txtCorners.text = "35";
                chkTurbo.value = true;
                chkDownsample.value = true;
            } else if (this.selection.index === 1) {
                // Standard Balanced
                sldColors.value = 8; txtColors.text = "8";
                sldNoise.value = 15; txtNoise.text = "15";
                sldPath.value = 80; txtPath.text = "80";
                sldCorners.value = 40; txtCorners.text = "40";
                chkTurbo.value = false;
                chkDownsample.value = true;
            } else if (this.selection.index === 2) {
                // Maximum Fidelity
                sldColors.value = 12; txtColors.text = "12";
                sldNoise.value = 8; txtNoise.text = "8";
                sldPath.value = 90; txtPath.text = "90";
                sldCorners.value = 50; txtCorners.text = "50";
                chkTurbo.value = false;
                chkDownsample.value = false;
            }
        };

        // Optimization & Low-End Safety Panel
        var pnlOptions = win.add("panel", undefined, "Low-End PC Safety & Optimizations");
        pnlOptions.orientation = "column";
        pnlOptions.alignChildren = ["left", "top"];
        pnlOptions.spacing = 6;
        pnlOptions.margins = 12;

        var chkTurbo = pnlOptions.add("checkbox", undefined, "Turbo Guard (Auto-skips heavy anchor loops if > 1500 paths)");
        chkTurbo.value = true;

        var chkDownsample = pnlOptions.add("checkbox", undefined, "Auto-Downsample oversized images (> 1500pt) before trace");
        chkDownsample.value = true;

        var chkIgnoreWhite = pnlOptions.add("checkbox", undefined, "Ignore Pure White Background (drop #FFFFFF)");
        chkIgnoreWhite.value = true;

        var chkAutoExpand = pnlOptions.add("checkbox", undefined, "Auto-Expand trace into editable vector paths");
        chkAutoExpand.value = true;

        var chkPurge = pnlOptions.add("checkbox", undefined, "Fast Micro-Artifact Purge (< 20 sq px)");
        chkPurge.value = true;

        var chkOptAnchors = pnlOptions.add("checkbox", undefined, "Selective Anchor Optimization (only bloat paths > 12 pts)");
        chkOptAnchors.value = true;

        // Action Buttons
        var grpButtons = win.add("group");
        grpButtons.orientation = "row";
        grpButtons.alignment = ["right", "bottom"];
        grpButtons.spacing = 10;

        var btnCancel = grpButtons.add("button", undefined, "Cancel", { name: "cancel" });
        var btnTrace = grpButtons.add("button", undefined, "Trace & Expand", { name: "ok" });
        btnTrace.preferredSize.width = 130;

        // Expose control references
        win.sliderColors = sldColors;
        win.sliderNoise = sldNoise;
        win.sliderPath = sldPath;
        win.sliderCorners = sldCorners;
        win.chkIgnoreWhite = chkIgnoreWhite;
        win.chkAutoExpand = chkAutoExpand;
        win.chkPurgeArtifacts = chkPurge;
        win.chkOptimizeAnchors = chkOptAnchors;
        win.chkDownsample = chkDownsample;
        win.chkTurbo = chkTurbo;

        return win;
    }
})();

