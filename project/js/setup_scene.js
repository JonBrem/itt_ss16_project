var canvas;
var engine;
var scene;

var camera;
var startingPoint;
var dragBugfixActive = false;

var ground;

var selectedPlaneName = "xz";
var selectedPlaneIndicators = [];
var selectedPlane = null;
var selectedPlaneMaterial;
var isMouseDown = false;

var scaleInitialYBottom = undefined;

var meshes = {};
var highlightedMesh;

var createScene = function() {
    // create a basic BJS Scene object
    var scene = new BABYLON.Scene(engine);

    // create a FreeCamera, and set its position to (x:0, y:5, z:-10)
    camera = new BABYLON.FreeCamera('camera1', new BABYLON.Vector3(0, 5,-10), scene);

    // target the camera to scene origin
    camera.setTarget(BABYLON.Vector3.Zero());

    // attach the camera to the canvas
    camera.attachControl(canvas, false);

    // create a basic light, aiming 0,1,0 - meaning, to the sky
    var light = new BABYLON.HemisphericLight('light1', new BABYLON.Vector3(0,1,0), scene);

    // create a built-in "ground" shape; its constructor takes the same 5 params as the sphere's one
    ground = BABYLON.Mesh.CreateGround('ground1', 6, 6, 2, scene);

    selectedPlaneMaterial = new BABYLON.StandardMaterial("selectedPlaneMaterial", scene);
    selectedPlaneMaterial.diffuseColor = new BABYLON.Color3(1, 0, 0);

    // return the created scene
    return scene;
}

jQuery(document).ready(function($) {
    canvas = document.getElementById('my_canvas');
    engine = new BABYLON.Engine(canvas, true);
    scene = createScene();
        
    engine.runRenderLoop(function() {
        scene.render();
    });

    window.addEventListener('resize', function() {
        engine.resize();
    });

    window.addEventListener("mousedown", onMouseDown);
    
    canvas.addEventListener("mouseup", onMouseUp, false);
    canvas.addEventListener("mousemove", onMouseMove, false);
});


function addMesh(data, id, images, type, transform, fileName) {
    try {
        BABYLON.SceneLoader.ImportMesh("", "", "data:" + data, scene, function (newMeshes) {
            newMeshes[0].id = id;
            newMeshes[0].mesh_type = type;
            meshes[id] = newMeshes[0];

            // only called when this is loaded
            if (transform != null) {
                loadTransformations(newMeshes[0], transform);
            } else {
                var bbox = newMeshes[0].getBoundingInfo().boundingBox;
                newMeshes[0].position.y -= bbox.minimumWorld.y;
            }

            // for loading only
            if (fileName != undefined && fileName != null) {
                newMeshes[0].modelFileName = fileName;
            }

            python_callback.js_mesh_loaded(id);
        }, function(a){}, function(b){}, images);
    } catch (e) {
        python_callback.js_mesh_load_error(id, e);
    }
}

function duplicateMesh(originalMeshId, newMeshId) {
    if (originalMeshId in meshes) {
        removeHighlight(originalMeshId);
        var newMesh = meshes[originalMeshId].clone("index: " + 1);

        newMesh.id = newMeshId;
        newMesh.mesh_type = meshes[originalMeshId].mesh_type;

        var bbox =  newMesh.getBoundingInfo().boundingBox;
        newMesh.position.x += bbox.extendSize.x * 2.2;

        meshes[newMeshId] = newMesh;
        python_callback.js_mesh_loaded(newMeshId);
    }
}

function loadTransformations(mesh, transform) {
    mesh.position.x = transform["pos"][0];
    mesh.position.y = transform["pos"][1];
    mesh.position.z = transform["pos"][2];

    mesh.rotation.x = transform["rot"][0];
    mesh.rotation.y = transform["rot"][1];
    mesh.rotation.z = transform["rot"][2];

    mesh.scaling.x = transform["scale"][0];
    mesh.scaling.y = transform["scale"][1];
    mesh.scaling.z = transform["scale"][2];
}

function setMeshPosition(id, x, y, z) {
    if (id in meshes) {
        meshes[id].setAbsolutePosition(new BABYLON.Vector3(x, y, z));
    }
}

function translateMeshByID(id, x, y, z) {
    if(id in meshes)
        x1 = '';
        y1 = '';
        z1 = '';

        if(x != 0)
            x1 = 'x';

        if(y != 0)
            y1 = 'y';

        if(z != 0)
            z1 = 'z';

        meshes[id].position.x += x;
        meshes[id].position.y += y;
        meshes[id].position.z += z;
}

function rotateMeshByID(id, x, y, z) {
    if(id in meshes) {
        x1 = '';
        y1 = '';
        z1 = '';

        if(x != 0)
            x1 = 'x';

        if(y != 0)
            y1 = 'y';

        if(z != 0)
            z1 = 'z';

        meshes[id].rotation.x = x;
        meshes[id].rotation.y = y;
        meshes[id].rotation.z = z;
    }
}

function scaleMeshByID(id, factorX, factorY, factorZ) {
    if(id in meshes) {
        if(factorX == 1 && factorY == 1 && factorZ == 1) return;

        // to keep the bottom equal (scale towards top, not from center out)
        if (scaleInitialYBottom == undefined || scaleInitialYBottom == null) {
            scaleInitialYBottom = meshes[id].getBoundingInfo().boundingBox.minimumWorld.y;
        }

        x1 = '';
        y1 = '';
        z1 = '';

        if(factorX != 1)
            x1 = 'x';

        if(factorY != 1)
            y1 = 'y';

        if(factorZ != 1)
            z1 = 'z';

        meshes[id].scaling.x = factorX;
        meshes[id].scaling.y = factorY;
        meshes[id].scaling.z = factorZ;

        var min_y_after = meshes[id].getBoundingInfo().boundingBox.minimumWorld.y;

        meshes[id].position.y += scaleInitialYBottom - min_y_after;

        python_callback.on_js_object_manipulation_performed(id, 'scaled',
                                                            x1, y1, z1);
    }
}

function onScaleEnd() {
    scaleInitialYBottom = undefined;
}

function highlight(obj_id, fromClick) {
    if (obj_id in meshes) {
        // http://www.babylonjs-playground.com/#E51MJ#8
        meshes[obj_id].outlineWidth = 0.05;
        meshes[obj_id].renderOutline = true;

        highlightedMesh = meshes[obj_id];

        if(fromClick) {
            setTimeout(function () {
                camera.detachControl(canvas);
                dragBugfixActive = true;
                startingPoint = highlightedMesh.getBoundingInfo().boundingBox.center;
            }, 0);
        }
    }
}

function removeHighlight(obj_id) {
    if (obj_id in meshes) {
        // http://www.babylonjs-playground.com/#E51MJ#8
        meshes[obj_id].outlineWidth = 0.0;
        meshes[obj_id].renderOutline = false;

        if (meshes[obj_id] == highlightedMesh) {
            highlightedMesh = null;

            camera.attachControl(canvas);
            startingPoint = null;
        }
    }
}

function getTranslationRotationScale(mesh_id) {
    trans = [meshes[mesh_id].position.x, meshes[mesh_id].position.y,
            meshes[mesh_id].position.z];

    rot = [meshes[mesh_id].rotation.x, meshes[mesh_id].rotation.y,
          meshes[mesh_id].rotation.z];

    scale = [meshes[mesh_id].scaling.x, meshes[mesh_id].scaling.y,
            meshes[mesh_id].scaling.z];


    python_callback.on_translation_rotation_scale_request(trans, rot, scale);
}

function removeMesh(mesh_id) {
    if (mesh_id in meshes) {
        meshes[mesh_id].dispose();
        delete meshes[mesh_id];
    }
}

function saveScene(identifier) {
    scene_data = {"meshes": []};

    for (id in meshes) {    
        scene_data["meshes"][scene_data["meshes"].length] = {
            "id": meshes[id].id,
            "type": meshes[id].mesh_type,
            "pos": [meshes[id].position.x, meshes[id].position.y, meshes[id].position.z],
            "rot": [meshes[id].rotation.x, meshes[id].rotation.y, meshes[id].rotation.z],
            "scale": [meshes[id].scaling.x, meshes[id].scaling.y, meshes[id].scaling.z],
            "fileName": meshes[id].modelFileName
        };
    }
    python_callback.save_state_result(JSON.stringify(scene_data), identifier);
}

function selectPlane(which) {
    selectedPlaneName = which;
}

// https://gamedevacademy.org/grabbing-3d-objects-with-the-mouse-babylonjs-series-part-11/
function onMouseDown(evt) {
    // 0 == left button. apparently also the accepted way to do this (without constants etc.)
    // https://developer.mozilla.org/en-US/docs/Web/API/MouseEvent/button
    if (evt.button == 0) {
        isMouseDown = true;

        var pickResult = scene.pick(evt.clientX, evt.clientY);
        if (pickResult.hit) {
            python_callback.on_object_clicked(pickResult.pickedMesh.id);
        } else {
            python_callback.on_object_clicked(null);
        }
    }
}

function selectPlane(which) {
    selectedPlaneName = which;
}

function createPlaneForSelection() {
    if (selectedPlane != null && selectedPlane != undefined) {
        selectedPlane.dispose();
        selectedPlaneIndicators[0].dispose();
        selectedPlaneIndicators[1].dispose();
    }

    initSelectedPlane();
    var bbox = highlightedMesh.getBoundingInfo().boundingBox;

    var camera_pos = camera.position;
    var mesh_pos = bbox.center;

    setSelectedPlanePosition(mesh_pos.x, mesh_pos.y, mesh_pos.z);

    if (selectedPlaneName == "xz") {
        if (camera_pos.y < mesh_pos.y) {
            setSelectedPlaneRotation(Math.PI, 0, 0);
        } else {
            setSelectedPlaneRotation(0, 0, 0);
        }
    } else if (selectedPlaneName == "xy") {
        if (camera_pos.z > mesh_pos.z) {
            setSelectedPlaneRotation(Math.PI * 3/2, Math.PI, 0);
        } else {
            setSelectedPlaneRotation(Math.PI * 3/2, 0, 0);
        }
    } else { // selectedPlaneName == "yz"
        if (camera_pos.x < mesh_pos.x) {
            setSelectedPlaneRotation(Math.PI * 3/2, Math.PI * 1/2, 0);
        } else {
            setSelectedPlaneRotation(Math.PI * 3/2, Math.PI * 3/2, 0);
        }
    }
}

function initSelectedPlane() {
    selectedPlane = BABYLON.Mesh.CreateGround('selectedPlane', 200, 200, 2, scene);
    selectedPlaneIndicators[0] = BABYLON.Mesh.CreateCylinder('selectedPlaneIndicator1', 200, 0.05, 0.05, 8, scene);
    selectedPlaneIndicators[1] = BABYLON.Mesh.CreateCylinder('selectedPlaneIndicator2', 200, 0.05, 0.05, 8, scene);

    selectedPlane.material = selectedPlaneMaterial;
    selectedPlaneIndicators[0].material = selectedPlaneMaterial;
    selectedPlaneIndicators[1].material = selectedPlaneMaterial;

    selectedPlane.visibility = 0.0;
    selectedPlaneIndicators[0].visibility = 0.3;
    selectedPlaneIndicators[1].visibility = 0.3;
}

function setSelectedPlanePosition(x, y, z) {
    selectedPlane.position.x = x;
    selectedPlane.position.y = y;
    selectedPlane.position.z = z;
    selectedPlaneIndicators[0].position.x = x;
    selectedPlaneIndicators[0].position.y = y;
    selectedPlaneIndicators[0].position.z = z;
    selectedPlaneIndicators[1].position.x = x;
    selectedPlaneIndicators[1].position.y = y;
    selectedPlaneIndicators[1].position.z = z;
}

function setSelectedPlaneRotation(x, y, z) {
    selectedPlane.rotation.x = x;
    selectedPlane.rotation.y = y;
    selectedPlane.rotation.z = z;
    selectedPlaneIndicators[0].rotation.x = x + Math.PI / 2;
    selectedPlaneIndicators[0].rotation.y = y;
    selectedPlaneIndicators[0].rotation.z = z;
    selectedPlaneIndicators[1].rotation.x = x + Math.PI / 2;
    selectedPlaneIndicators[1].rotation.y = y;
    selectedPlaneIndicators[1].rotation.z = z + Math.PI / 2;
}

function onMouseUp() {
    isMouseDown = false;

    if (selectedPlane != null && selectedPlane != undefined) {
        selectedPlane.dispose();
        selectedPlaneIndicators[0].dispose();
        selectedPlaneIndicators[1].dispose();
    }

    if (startingPoint) {
        camera.attachControl(canvas);
        startingPoint = null;
        return;
    }
}

function onMouseMove(evt) {
    if (isMouseDown && highlightedMesh != null && dragBugfixActive) {
        dragBugfixActive = false;
        python_callback.on_js_obj_drag_start(highlightedMesh.id);
        createPlaneForSelection();
    }

    if (!startingPoint) {
        return;
    }

    var current = getPositionAlongSelectedPlane(evt);

    if (!current) {
        return;
    }

    var diff = current.subtract(startingPoint);
    highlightedMesh.position.addInPlace(diff);

    startingPoint = current;
}


function getPositionAlongSelectedPlane(evt) {
    // Use a predicate to get position on the ground
    var pickinfo = scene.pick(scene.pointerX, scene.pointerY, function (mesh) { return mesh == selectedPlane; });
    if (pickinfo.hit) {
        // strangely, the point is not always _in_ the plane ._.
        var point = pickinfo.pickedPoint;

        if (selectedPlaneName == "xy") {
            point.z = selectedPlane.position.z;
        } else if (selectedPlaneName == "xz") {
            point.y = selectedPlane.position.y;
        } else { // selectedPlaneName == "yz"
            point.x = selectedPlane.position.x;
        }

        return point;
    }

    return null;
}

function setCameraToDefault() {
    camera.position.x = 0;
    camera.position.y = 5;
    camera.position.z = -10;

    camera.setTarget(new BABYLON.Vector3(0, 0, 0));
}
