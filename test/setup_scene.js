var canvas;
var engine;
var scene;

var meshes = {};

var createScene = function() {
    // create a basic BJS Scene object
    var scene = new BABYLON.Scene(engine);

    // create a FreeCamera, and set its position to (x:0, y:5, z:-10)
    var camera = new BABYLON.FreeCamera('camera1', new BABYLON.Vector3(0, 5,-10), scene);

    // target the camera to scene origin
    camera.setTarget(BABYLON.Vector3.Zero());

    // attach the camera to the canvas
    camera.attachControl(canvas, false);

    // create a basic light, aiming 0,1,0 - meaning, to the sky
    var light = new BABYLON.HemisphericLight('light1', new BABYLON.Vector3(0,1,0), scene);

    // create a built-in "ground" shape; its constructor takes the same 5 params as the sphere's one
    var ground = BABYLON.Mesh.CreateGround('ground1', 6, 6, 2, scene);

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

    window.addEventListener("click", onClick);
    
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

        python_callback.on_js_object_manipulation_performed(id, 'translated',
                                                            x1, y1, z1);
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

        python_callback.on_js_object_manipulation_performed(id, 'rotated',
                                                            x1, y1, z1);
    }
}

function scaleMeshByID(id, factorX, factorY, factorZ) {
    if(id in meshes) {
        if(factorX == 1 && factorY == 1 && factorZ == 1) return;

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

        python_callback.on_js_object_manipulation_performed(id, 'scaled',
                                                            x1, y1, z1);
    }
}

// https://gamedevacademy.org/grabbing-3d-objects-with-the-mouse-babylonjs-series-part-11/
function onClick(evt) {
    var pickResult = scene.pick(evt.clientX, evt.clientY);
    if (pickResult.hit) {
        python_callback.on_object_clicked(pickResult.pickedMesh.id);
    } else {
        python_callback.on_object_clicked(null);
    }
}

function highlight(obj_id) {
    if (obj_id in meshes) {
        // http://www.babylonjs-playground.com/#E51MJ#8
        meshes[obj_id].outlineWidth = 0.05;
        meshes[obj_id].renderOutline = true;
    }
}

function removeHighlight(obj_id) {
    if (obj_id in meshes) {
        // http://www.babylonjs-playground.com/#E51MJ#8
        meshes[obj_id].outlineWidth = 0.0;
        meshes[obj_id].renderOutline = false;
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
        delete meshes["mesh_id"];
    }
}

function saveScene() {
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

    python_callback.save_state_result(JSON.stringify(scene_data));
}

// @TODO do we need those? click/mouse press might be enough for selecting
// maybe we'll need it if we want to drag things on screen...
function onMove(evt) {

}

function onRelease(evt) {

}
