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


function addMesh(data, id) {
    try {
        BABYLON.SceneLoader.ImportMesh("", "", "data:" + data, scene, function (newMeshes) {
            newMeshes[0].id = id;
            meshes[id] = newMeshes[0];
            python_callback.js_mesh_loaded(id);
            python_callback.on_js_console_log(meshes[id].position);
        });
    } catch (e) {
        python_callback.js_mesh_load_error(id, e);
    }
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

        python_callback.on_js_console_log('translation: ' + meshes[id].position);
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

        python_callback.on_js_console_log('rotation: ' + meshes[id].rotation);
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

        meshes[id].scaling.x *= factorX;
        meshes[id].scaling.y *= factorY;
        meshes[id].scaling.z *= factorZ;

        python_callback.on_js_object_manipulation_performed(id, 'scaled',
                                                            x1, y1, z1);

        python_callback.on_js_console_log('scaling: ' + meshes[id].scaling);
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
            meshes[mesh_id].position.z]

    rot = [meshes[mesh_id].rotation.x, meshes[mesh_id].rotation.y,
          meshes[mesh_id].rotation.z]

    scale = [meshes[mesh_id].scaling.x, meshes[mesh_id].scaling.y,
            meshes[mesh_id].scaling.z]


    python_callback.on_translation_rotation_scale_request(trans, rot, scale)
}

// @TODO do we need those? click/mouse press might be enough for selecting
// maybe we'll need it if we want to drag things on screen...
function onMove(evt) {

}

function onRelease(evt) {

}
