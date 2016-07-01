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
    
});


function addMesh(data, id) {
    try {
        BABYLON.SceneLoader.ImportMesh("", "", "data:" + data, scene, function (newMeshes) {
            newMeshes[0].id = id;
            meshes[id] = newMeshes[0];
            python_callback.js_mesh_loaded(id);
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
