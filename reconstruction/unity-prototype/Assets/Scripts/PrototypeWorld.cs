using System.Collections.Generic;
using UnityEngine;

namespace Rabron.Prototype
{
    /// <summary>Procedural original blockout. Nothing is loaded from ROB RUN bundles.</summary>
    public static class PrototypeWorld
    {
        private static readonly Dictionary<Color, Material> Palette =
            new Dictionary<Color, Material>();

        public static IReadOnlyList<InteractionMarker> Create(Transform parent,
                                                               out ThirdPersonMotor player,
                                                               out CashPilePresenter cashPile,
                                                               out GuardSensor guard)
        {
            var stations = new List<InteractionMarker>(21);
            var asphalt = Hex("#242A34");
            var concrete = Hex("#56616F");
            var wall = Hex("#3E4858");
            var wood = Hex("#614835");

            Cube(parent, "Ground", new Vector3(0, -0.65f, -6),
                 new Vector3(110, 1, 160), Hex("#34463B"));
            Cube(parent, "Road", new Vector3(0, -0.1f, -6),
                 new Vector3(13, 0.18f, 125), asphalt);

            for (int side = -1; side <= 1; side += 2)
            {
                Cube(parent, "Sidewalk", new Vector3(side * 8.25f, -0.06f, -6),
                     new Vector3(3.2f, 0.22f, 120), concrete);
                for (int z = -45; z <= 45; z += 18)
                {
                    Cube(parent, "Streetlight post", new Vector3(side * 7, 3, z),
                         new Vector3(0.18f, 6, 0.18f), concrete);
                    Cube(parent, "Streetlight head", new Vector3(side * 7, 6.1f, z),
                         new Vector3(1.1f, 0.3f, 1.1f), Hex("#F4D18A"));
                }
            }

            // Small heist building. 4m central opening in the front wall.
            Cube(parent, "Robbery floor", new Vector3(0, -0.06f, 27),
                 new Vector3(17, 0.22f, 20), concrete);
            Cube(parent, "Robbery back", new Vector3(0, 2.8f, 37),
                 new Vector3(17, 5.6f, 0.8f), wall);
            Cube(parent, "Robbery left", new Vector3(-8.5f, 2.8f, 27),
                 new Vector3(0.8f, 5.6f, 20), wall);
            Cube(parent, "Robbery right", new Vector3(8.5f, 2.8f, 27),
                 new Vector3(0.8f, 5.6f, 20), wall);
            Cube(parent, "Robbery entrance left", new Vector3(-5.4f, 2.8f, 17),
                 new Vector3(6.2f, 5.6f, 0.8f), wall);
            Cube(parent, "Robbery entrance right", new Vector3(5.4f, 2.8f, 17),
                 new Vector3(6.2f, 5.6f, 0.8f), wall);
            Cube(parent, "Art pedestal", new Vector3(-3, 0.6f, 26),
                 new Vector3(1.6f, 1.2f, 1.6f), wood);
            Cube(parent, "Watch display", new Vector3(3, 0.6f, 29),
                 new Vector3(1.6f, 1.2f, 1.6f), wood);
            // Real waist-high cover between the front approach and the guard.
            // A crouched capsule can hide behind this opaque BoxCollider;
            // standing exposes the upper body, and both sides remain walkable.
            Cube(parent, "Warehouse stealth cover", new Vector3(0f, 0.75f, 30f),
                 new Vector3(2.8f, 1.5f, 0.6f), wood);

            // Original primitive guard, not an extracted game NPC. He faces
            // the entrance and has a configurable demo-only sight cone.
            var security = new GameObject("Warehouse guard");
            security.transform.SetParent(parent, false);
            security.transform.position = new Vector3(0f, 0f, 33f);
            security.transform.rotation = Quaternion.Euler(0f, 180f, 0f);
            var guardBody = GameObject.CreatePrimitive(PrimitiveType.Capsule);
            guardBody.name = "Guard placeholder mesh";
            guardBody.transform.SetParent(security.transform, false);
            guardBody.transform.localPosition = Vector3.up;
            guardBody.GetComponent<Renderer>().sharedMaterial = Swatch(Hex("#BD5252"));
            guardBody.GetComponent<Collider>().isTrigger = true;
            guard = security.AddComponent<GuardSensor>();

            // Distinct fence, money pickup, laundering and ATM locations.
            Cube(parent, "Fence stage", new Vector3(-19, 0.25f, 1),
                 new Vector3(8, 0.5f, 9), concrete);
            Cube(parent, "Fence counter", new Vector3(-19, 1.05f, 0),
                 new Vector3(5, 1, 1.3f), wood);

            // Cash is not in the wallet until the player explicitly picks it up.
            // This original placeholder mesh is visual-only: the economy lives
            // in HeistSession, and no actual game models are imported.
            var money = new GameObject("Fence cash waiting on counter");
            money.transform.SetParent(parent, false);
            var cashColor = Hex("#6FBF88");
            for (int i = 0; i < 4; i++)
            {
                var bundle = Cube(money.transform, "Cash bundle " + (i + 1),
                    new Vector3(-20.1f + i * 0.72f, 1.64f, 0),
                    new Vector3(0.62f, 0.12f, 0.42f), cashColor);
                bundle.GetComponent<Collider>().enabled = false;
            }
            cashPile = money.AddComponent<CashPilePresenter>();
            cashPile.SetAmount(0);
            Cube(parent, "Laundering workbench", new Vector3(20, 0.9f, 1),
                 new Vector3(5, 1.8f, 2), Hex("#647B81"));
            // Civilian-only alternative to the robbery. Two separate walkable
            // roadside kiosks, not an imported delivery or reference-game asset.
            Cube(parent, "Courier dispatch kiosk", new Vector3(-16, 0.7f, -17),
                 new Vector3(2.5f, 1.4f, 3), Hex("#B18C5A"));
            Cube(parent, "Courier recipient kiosk", new Vector3(16, 0.7f, -17),
                 new Vector3(2.5f, 1.4f, 3), Hex("#79A98F"));
            // Original small local custody waypoint, not reference-game police art.
            Cube(parent, "Police custody desk", new Vector3(20, 0.65f, -39),
                 new Vector3(2.5f, 1.3f, 2), Hex("#5D7192"));
            Cube(parent, "ATM booth", new Vector3(0, 1.35f, -24),
                 new Vector3(2, 2.7f, 1.1f), Hex("#367C9F"));
            Cube(parent, "ATM screen", new Vector3(0, 1.75f, -23.41f),
                 new Vector3(1.35f, 0.9f, 0.1f), Hex("#81DCFD"));

            // One deliberately plain, physically bounded practice car.
            // Vehicle position is transient; currency and saved role stay in
            // HeistSession, and no original game vehicle media is imported.
            var car = new GameObject("Driveable demo car");
            car.transform.SetParent(parent, false);
            car.transform.position = new Vector3(4f, 0.1f, -15f);
            var carBody = car.AddComponent<CharacterController>();
            carBody.height = 1.9f;
            carBody.radius = 0.95f;
            carBody.center = new Vector3(0f, 0.95f, 0f);
            carBody.stepOffset = 0.4f;

            var paint = Hex("#CC8A55");
            var shell = Cube(car.transform, "Vehicle shell",
                new Vector3(4f, 0.75f, -15f), new Vector3(2f, 0.7f, 3.3f), paint);
            shell.GetComponent<Collider>().enabled = false;
            var roof = Cube(car.transform, "Vehicle cabin",
                new Vector3(4f, 1.3f, -15.35f), new Vector3(1.55f, 0.55f, 1.7f),
                Hex("#61849C"));
            roof.GetComponent<Collider>().enabled = false;
            for (int side = -1; side <= 1; side += 2)
            {
                for (int axle = -1; axle <= 1; axle += 2)
                {
                    var wheel = Cube(car.transform, "Vehicle wheel",
                        new Vector3(4f + side * 1.02f, 0.38f, -15f + axle * 1.1f),
                        new Vector3(0.3f, 0.58f, 0.6f), Hex("#22272D"));
                    wheel.GetComponent<Collider>().enabled = false;
                }
            }
            car.AddComponent<PrototypeVehicle>();
            // Enter marker follows the moving car; it is not a static
            // road-side teleport or a second vehicle simulation.
            Station(car.transform, stations, StationAction.VehicleEnter,
                    "Enter practice car", new Vector3(1.5f, 0f, -16f), "#E9BD8A");

            Station(parent, stations, StationAction.ReleaseCustody, "Leave police custody",
                    new Vector3(16, 0, -38), "#98B6DD");
            Station(parent, stations, StationAction.CourierPickup, "Collect legal delivery parcel",
                    new Vector3(-12, 0, -17), "#B9D09A");
            Station(parent, stations, StationAction.CourierDropoff, "Deliver legal parcel",
                    new Vector3(12, 0, -17), "#86CFB1");
            Station(parent, stations, StationAction.CourierCancel, "Return parcel without payment",
                    new Vector3(-12, 0, -21), "#B9D09A");
            Station(parent, stations, StationAction.Scout, "Scout building",
                    new Vector3(-3, 0, 11), "#80D6F2");
            Station(parent, stations, StationAction.Mask, "Put on criminal mask",
                    new Vector3(4, 0, 11), "#E78D88");
            Station(parent, stations, StationAction.BeginRobbery, "Begin heist",
                    new Vector3(0, 0, 19), "#E3AF57");
            Station(parent, stations, StationAction.Artwork, "Take artwork",
                    new Vector3(-3, 1.3f, 26), "#F2BD64");
            Station(parent, stations, StationAction.Watch, "Take watch",
                    new Vector3(3, 1.3f, 29), "#F2BD64");
            // Close enough to approach from the front of the low cover:
            // standing can reach over it, crouching must flank instead.
            // Keep the station clear of the guard placeholder's trigger mesh.
            Station(parent, stations, StationAction.ControlStaff,
                    "Control guard without raising alarm",
                    new Vector3(-1.3f, 0f, 31.9f), "#D99BB5");
            Station(parent, stations, StationAction.Escape, "Escape with loot",
                    new Vector3(0, 0, 5), "#86C8A5");
            Station(parent, stations, StationAction.WithdrawEmptyHanded,
                    "Withdraw from heist without payment",
                    new Vector3(2.2f, 0, 5), "#C0AE84");
            Station(parent, stations, StationAction.Fence, "Sell loot at fence",
                    new Vector3(-19, 0.65f, -2.3f), "#D6BB83");
            Station(parent, stations, StationAction.CollectCash, "Collect cash on counter",
                    new Vector3(-19, 0f, 1.65f), "#E0DB7B");
            Station(parent, stations, StationAction.Launder, "Start laundering",
                    new Vector3(20, 0, 3.5f), "#80C9B9");
            Station(parent, stations, StationAction.OpenBank, "Open bank account",
                    new Vector3(2.7f, 0, -24), "#73B5F2");
            Station(parent, stations, StationAction.Deposit, "Deposit clean cash",
                    new Vector3(-2.7f, 0, -24), "#73B5F2");
            Station(parent, stations, StationAction.ExitCity, "Leave city and clear mask",
                    new Vector3(-2, 0, -32), "#D5A8DA");
            Station(parent, stations, StationAction.EnterCity, "Return to city",
                    new Vector3(-2, 0, -43), "#D5A8DA");
            Station(parent, stations, StationAction.Reset, "Start the next heist",
                    new Vector3(-8.5f, 0, -16), "#91CD92");

            var actor = new GameObject("Local player");
            actor.transform.SetParent(parent, false);
            actor.transform.position = new Vector3(0, 0.12f, -15);
            var controller = actor.AddComponent<CharacterController>();
            controller.height = 1.9f;
            controller.radius = 0.36f;
            controller.center = new Vector3(0, 0.95f, 0);
            // The fence has a raised 0.5m platform. The default 0.3m
            // CharacterController step cannot reach its cash pickup.
            controller.stepOffset = 0.65f;

            var body = GameObject.CreatePrimitive(PrimitiveType.Capsule);
            body.name = "Player mesh";
            body.transform.SetParent(actor.transform, false);
            body.transform.localPosition = new Vector3(0, 0.95f, 0);
            body.transform.localScale = new Vector3(0.7f, 0.95f, 0.7f);
            // Editor-mode geometry smoke tests must not queue destruction.
            var bodyCollider = body.GetComponent<Collider>();
            if (Application.isPlaying)
                Object.Destroy(bodyCollider);
            else
                Object.DestroyImmediate(bodyCollider);
            body.GetComponent<Renderer>().sharedMaterial = Swatch(Hex("#F2B76D"));
            player = actor.AddComponent<ThirdPersonMotor>();

            // A small carried parcel attaches to the actor, never to the
            // transaction ledger. No active collider can block the camera,
            // station reachability or movement.
            var parcel = GameObject.CreatePrimitive(PrimitiveType.Cube);
            parcel.name = "Carried courier parcel (visual only)";
            parcel.transform.SetParent(actor.transform, false);
            parcel.transform.localPosition = new Vector3(0.56f, 1.18f, 0.18f);
            parcel.transform.localScale = new Vector3(0.5f, 0.42f, 0.48f);
            parcel.GetComponent<Collider>().enabled = false;
            parcel.GetComponent<Renderer>().sharedMaterial = Swatch(Hex("#C79A62"));
            parcel.AddComponent<CourierParcelPresenter>().SetCarrying(false);

            var daylight = new GameObject("Daylight");
            daylight.transform.SetParent(parent, false);
            daylight.transform.rotation = Quaternion.Euler(48, -32, 0);
            var light = daylight.AddComponent<Light>();
            light.type = LightType.Directional;
            light.intensity = 1.3f;
            RenderSettings.ambientLight = Hex("#929DA6");
            return stations;
        }

        private static void Station(Transform parent, ICollection<InteractionMarker> stations,
                                    StationAction action, string label, Vector3 position,
                                    string color)
        {
            var pillar = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
            pillar.transform.SetParent(parent, false);
            pillar.transform.position = position + Vector3.up * 1.2f;
            pillar.transform.localScale = new Vector3(0.65f, 1.2f, 0.65f);
            pillar.GetComponent<Renderer>().sharedMaterial = Swatch(Hex(color));
            pillar.GetComponent<Collider>().isTrigger = true;
            var marker = pillar.AddComponent<InteractionMarker>();
            marker.Configure(action, label);
            stations.Add(marker);
        }

        private static GameObject Cube(Transform parent, string label, Vector3 center,
                                 Vector3 size, Color color)
        {
            var primitive = GameObject.CreatePrimitive(PrimitiveType.Cube);
            primitive.name = label;
            primitive.transform.SetParent(parent, false);
            primitive.transform.position = center;
            primitive.transform.localScale = size;
            primitive.GetComponent<Renderer>().sharedMaterial = Swatch(color);
            return primitive;
        }

        private static Material Swatch(Color color)
        {
            if (Palette.TryGetValue(color, out var material))
                return material;
            var shader = Shader.Find("Standard") ?? Shader.Find("Universal Render Pipeline/Lit")
                         ?? Shader.Find("Unlit/Color");
            if (shader == null)
                return null!;
            material = new Material(shader) { color = color };
            Palette.Add(color, material);
            return material;
        }

        private static Color Hex(string hex) =>
            ColorUtility.TryParseHtmlString(hex, out Color color) ? color : Color.white;
    }
}
