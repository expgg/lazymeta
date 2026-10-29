/**
 * LazyMeta: Adobe Illustrator Batch Auto-Trace & Expand Script
 * 
 * Instructions:
 * 1. Open Adobe Illustrator.
 * 2. Go to: File -> Scripts -> Other Script... (Ctrl+F12 / Cmd+F12)
 * 3. Select this file: `illustrator_batch_trace.jsx`
 * 4. Select your folder containing the generated images (e.g. `images/`).
 * 5. Illustrator will automatically trace, ignore white backgrounds, expand, and save clean vectors!
 */

#target illustrator

function batchTraceAndExpand() {
    var folder = Folder.selectDialog("Select the folder containing your LazyMeta images (01.jpg - 90.jpg):");
    if (!folder) return;

    var outputFolder = new Folder(folder.fsName + "/vectorized");
    if (!outputFolder.exists) {
        outputFolder.create();
    }

    var files = folder.getFiles(function(f) {
        return f instanceof File && f.name.match(/\.(jpg|jpeg|png|webp)$/i);
    });

    if (files.length === 0) {
        alert("No image files found in the selected folder!");
        return;
    }

    var confirmed = confirm("Found " + files.length + " image(s).\nProceed with batch auto-trace and vector expansion?");
    if (!confirmed) return;

    var processed = 0;

    for (var i = 0; i < files.length; i++) {
        var file = files[i];
        try {
            var doc = app.open(file);

            // Select placed image
            if (doc.placedItems.length > 0 || doc.rasterItems.length > 0) {
                var item = doc.rasterItems.length > 0 ? doc.rasterItems[0] : doc.placedItems[0];
                item.selected = true;

                // Create tracing
                var trace = item.trace();
                var opt = trace.tracingOptions;

                // Optimize settings for clean silkscreen vector trace
                opt.tracingModeType = TracingModeType.TRACINGMODECOLOR;
                opt.colorFidelity = 80;
                opt.maxColors = 5;
                opt.ignoreWhite = true;
                opt.noise = 15;
                opt.pathFitting = 80;
                opt.cornerAngle = 40;

                // Expand trace into actual vector paths
                app.executeMenuCommand("Live Trace Expand");

                // Save as clean SVG or AI
                var exportName = file.name.replace(/\.[^\.]+$/, ".ai");
                var saveFile = new File(outputFolder.fsName + "/" + exportName);
                doc.saveAs(saveFile, new IllustratorSaveOptions());
                doc.close(SaveOptions.DONOTSAVECHANGES);

                processed++;
            } else {
                doc.close(SaveOptions.DONOTSAVECHANGES);
            }
        } catch (e) {
            // Continue on single file error
        }
    }

    alert("Batch Auto-Trace Complete!\nSuccessfully vectorized " + processed + " of " + files.length + " images.\nSaved to: " + outputFolder.fsName);
}

batchTraceAndExpand();
