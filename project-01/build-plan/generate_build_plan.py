"""Generate original EV3 planning diagrams and a printable assembly companion.

Requires matplotlib. Run from any directory with python generate_build_plan.py.
LEGO's linked manuals supply the verified hole-by-hole assembly instructions.
"""
from pathlib import Path
import textwrap

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle, Circle

OUT = Path(__file__).resolve().parent
BLUE, TEAL, ORANGE = '#24598a', '#167d86', '#b55c20'
BASE = 'https://assets.education.lego.com/v3/assets/blt293eea581807678a/bltc8481dd2666822ff/5f8801e3f4f4cf0fa39d2fef/ev3-rem-driving-base.pdf'
COLOR = 'https://assets.education.lego.com/v3/assets/blt293eea581807678a/blt8b300493e30608e9/5f8801dfb8b59a77a945d13c/ev3-rem-color-sensor-down-driving-base.pdf'
GYRO = 'https://assets.education.lego.com/v3/assets/blt293eea581807678a/bltc961107e6587a579/5f8801dd3b19d21d4a6085bf/ev3-gyro-sensor-driving-base.pdf'
SENSOR = 'https://education.lego.com/en-us/lessons/ev3-space/turn-using-sensor/'
LIGHT = 'https://ev3-help-online.api.education.lego.com/Education/en-gb/page.html?Path=editor%2FUsingSensors_Color.html'

plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'svg.fonttype': 'none'})
page_no = 0

def page(title, subtitle):
    global page_no
    page_no += 1
    fig = plt.figure(figsize=(8.27, 11.69), facecolor='white')
    fig.text(.075, .952, 'PROJECT 01 / EV3 NAVIGATION', color=TEAL, fontsize=10, weight='bold')
    fig.text(.075, .914, title, fontsize=21, weight='bold', color=BLUE)
    fig.text(.075, .883, subtitle, fontsize=9, color='#555555')
    fig.text(.075, .035, 'Build companion v2 / 22 Oct 2026 / physical assembly not yet validated', fontsize=8, color='#666666')
    fig.text(.925, .035, str(page_no), ha='right', fontsize=9)
    return fig

def block(fig, y, title, body, width=91):
    fig.text(.075, y, title, weight='bold', color=TEAL, fontsize=11)
    y -= .026
    for para in body.split('\n'):
        lines = textwrap.wrap(para, width=width) if para else ['']
        for line in lines:
            fig.text(.075, y, line, fontsize=10)
            y -= .0175
        y -= .006
    return y - .010

def link(fig, y, label, url):
    fig.text(.075, y, label + '  [open official source]', color=BLUE, fontsize=10, url=url)
    return y - .029

def rect(ax, x, y, w, h, label, color='#e4edf4'):
    ax.add_patch(Rectangle((x,y),w,h,facecolor=color,edgecolor=BLUE,lw=1.5))
    ax.text(x+w/2,y+h/2,label,ha='center',va='center',fontsize=9)

def arrow(ax, start, end, label=None, color=TEAL):
    ax.annotate('',xy=end,xytext=start,arrowprops={'arrowstyle':'->','color':color,'lw':1.5})
    if label:
        ax.text(end[0]+4,end[1]+4,label,color=color,fontsize=9)

def diagram_axes(fig, bounds):
    ax=fig.add_axes(bounds)
    ax.set_aspect('equal'); ax.axis('off')
    return ax

def save(pdf, fig, svg=None):
    if svg:
        path = OUT / svg
        fig.savefig(path, format='svg')
        path.write_text('\n'.join(line.rstrip() for line in path.read_text().splitlines()) + '\n')
    pdf.savefig(fig)
    plt.close(fig)

def main():
  with PdfPages(OUT/'ev3-build-plan.pdf') as pdf:
    fig=page('Build strategy and parts', 'A repeatable driving base, with an explicit assembly and measurement sequence.')
    y=block(fig,.835,'How to use this guide',
      'Build the official Driving Base first, then the gyro module. Add color sensing only '
      'after baseline tests pass. Those manuals '
      'supply exact LEGO parts, holes, pin positions, and axle lengths. This companion supplies '
      'the build order, integration checks, original layout sketches, and calibration procedure.\n'
      'The sketches are functional schematics, not LEGO CAD or dimensioned fabrication drawings. '
      'The custom combined layout is a proposed arrangement: check available holes, parts, and '
      'clearance physically. No extra-kit parts are assumed available. Keep the official geometry '
      'unless a measured problem justifies changing it.')
    y=block(fig,y,'Gather before assembly',
      'Core: 1 EV3 brick with battery; 2 large motors; 2 matching wheels and tires; the kit ball '
      'caster assembly; the beams, axles, bushes, connectors and pins specified in the base manual.\n'
      'Sensing: 1 EV3 gyro; 1 EV3 color sensor; the mounting parts specified in both module manuals; '
      '4 cables total for 2 motors and 2 sensors. Choose lengths that reach without dragging.\n'
      'Integration: reserve leftover beams and friction pins for bracing and cable retention. '
      'Check the module parts callouts against what remains after building the base; the combined '
      'parts budget and simultaneous attachment points have not been physically verified.\n'
      'Tools for testing: ruler or tape measure, square, representative floor surface, temporary '
      'test marks, notebook, and a laptop for logging. Do not add marks to the actual course '
      'without permission. A second color sensor is an optional later upgrade, not required.')
    y=block(fig,y,'Assembly references: use these alongside the companion',
      'All three manuals below are official LEGO documents. Follow their illustrated sequences '
      'in full; they are linked, rather than reproduced in this repository.')
    y=link(fig,y,'1. Driving Base / 46 PDF pages',BASE)
    y=link(fig,y,'2. Color Sensor Down / 7 PDF pages',COLOR)
    y=link(fig,y,'3. Gyro Sensor / 10 PDF pages',GYRO)
    save(pdf,fig)

    fig=page('Minimum build and decision order', 'Review revision / adapt the official base before considering a new chassis.')
    y=block(fig,.835,'Build A: the engineering baseline',
      'Use the unmodified official Driving Base, two large motors and encoders, battery, '
      'ball caster, and official gyro mount. Secure its three cables. Do not add a second '
      'color sensor, ultrasonic scanner, extra gear train, or custom chassis initially.\n'
      'Do not move the brick or change wheel supports to imitate the layout sketches. '
      'Reseat loose pins first. Add bracing only where a specific joint visibly moves; '
      'otherwise it can introduce twist. The assignment does not require a goal sensor.')
    y=block(fig,y,'Gate 1: prove the base before accessories',
      'Confirm motor/gyro signs, repeatable starting alignment, stable gyro startup, free '
      'caster motion, and no wheel rub. Repeat straight drives, both turn directions, '
      'and complete routes at realistic durations. Record independent physical errors. '
      'Ten trials are an initial screen, not a reliability certificate.\n'
      'Compare smooth low and moderate speeds. Extremely slow motion extends run time '
      'and gyro-bias exposure; choose the better measured full-route performance. '
      'Slow for turns and endpoints. Keep pauses brief and purposeful.')
    y=block(fig,y,'Build B: optional color sensing',
      'Add the official downward module only if it fits alongside the gyro with available '
      'parts and preserves clearance. Its first job is goal confirmation in the mapped '
      'goal region. It cannot protect the full robot width from flat obstacles.\n'
      'Start with seam correction DISABLED. Evaluate it only if route error exceeds '
      'clearance and actual seams are detectable. A failed seam experiment must not '
      'delay baseline testing. Recalibrate and rerun routes after payload/mount changes.\n'
      'The combined mounts and parts budget remain unverified. If modules conflict, '
      'retain Build A. Do not improvise a fragile bracket just to complete Build B.')
    y=block(fig,y,'When a task-specific mechanical modification is justified',
      'If the sensor boom dominates turning radius, shorten its mount while retaining '
      'lens clearance and a rigid attachment, then remeasure offsets and R. If a joint '
      'flexes, brace that joint. If the caster snags seams, inspect its clearance and '
      'loading. Change one thing at a time and repeat the failed test.\n'
      'A new chassis is justified only when the stock geometry cannot meet measured '
      'clearance or traction needs. Until then, stock geometry is the simpler baseline. '
      'Custom hole-by-hole instructions require a verified parts inventory and physical fit.')
    block(fig,y,'Limits of the baseline',
      'Gyro plus encoders provide finite-run dead reckoning. They cannot recover all '
      'wheel slip or guarantee every arbitrary course. The assignment acknowledges '
      'occasional failures; our acceptance depends on repeated full-route tests and '
      'clearance reserve, not on sensor specifications alone.')
    save(pdf,fig)

    fig=page('01 / Top-view layout', 'Functional layout / not to scale / use official manuals for exact LEGO connections.')
    ax=diagram_axes(fig,[.08,.40,.84,.44])
    ax.set_xlim(-175,195); ax.set_ylim(-155,155)
    ax.add_patch(Circle((0,0),140,fill=False,ls='--',ec=ORANGE,lw=1.2))
    rect(ax,-95,-56,180,112,'','#f0f3f5')
    rect(ax,-68,-40,115,80,'')
    ax.text(-10,22,'EV3 brick\nlow, centered',ha='center',va='center',fontsize=9)
    rect(ax,-30,56,55,22,'L motor')
    rect(ax,-30,-78,55,22,'R motor')
    rect(ax,-28,78,56,18,'L wheel','#333333')
    rect(ax,-28,-96,56,18,'R wheel','#333333')
    # Light labels keep the dark wheel markings legible.
    ax.text(0,87,'L wheel',ha='center',va='center',color='white',fontsize=9)
    ax.text(0,-87,'R wheel',ha='center',va='center',color='white',fontsize=9)
    ax.add_patch(Circle((-110,0),12,fc='#d7dce0',ec=BLUE))
    ax.text(-112,-27,'Caster',ha='center',fontsize=9)
    rect(ax,55,8,24,30,'G','#cbe9dd')
    rect(ax,95,-15,30,30,'','#ffe1c9')
    ax.text(110,9,'C',ha='center',va='center',fontsize=9)
    ax.plot([85,95],[0,0],color=BLUE,lw=3)
    ax.plot([0,0],[-105,105],ls=':',color=BLUE)
    ax.plot(0,0,'+',ms=14,color=ORANGE)
    arrow(ax,(0,0),(160,0),'+x forward')
    arrow(ax,(0,0),(0,120),'+y left')
    ax.annotate('',xy=(-150,87),xytext=(-150,-87),arrowprops={'arrowstyle':'<->','color':BLUE})
    ax.text(-158,0,'Track b',rotation=90,ha='center',va='center',color=BLUE)
    ax.text(65,-150,'Dashed circle: turning envelope',color=ORANGE,ha='center',fontsize=9)
    y=block(fig,.355,'Reference points',
      'O is the midpoint between the drive-wheel contact centers. Define robot pose here; do not '
      'silently use the brick center or front sensor as the position reference. +x is forward; '
      '+y is left; positive heading is counterclockwise when viewed from above.\n'
      'G = gyro on a rigid mount; exact position may differ. C = OPTIONAL downward color sensor, drawn '
      'on the centerline for clarity. If the official module is offset sideways, keep it and '
      'measure that offset. Do not rebuild a sound module just to match this sketch.')
    block(fig,y,'Clearance rule',
      'Measure R from O to the farthest protruding point, including cables. Use a circle of '
      'radius R plus an error allowance for conservative planning and in-place turns. A 0.61 m '
      'corridor admits this envelope only when 2(R + allowance) < 0.61 m. This is a design check, '
      'not a measured claim about the base.')
    save(pdf,fig,'01-top-layout.svg')

    fig=page('02 / Side and front views', 'Sensor orientation and support geometry / conceptual positions / no fixed dimensions.')
    ax=diagram_axes(fig,[.075,.58,.85,.26]);ax.set_xlim(-155,175);ax.set_ylim(-25,100)
    ax.plot([-150,170],[-5,-5],color='#666666')
    rect(ax,-85,27,160,12,'Frame')
    rect(ax,-65,39,100,48,'EV3 brick')
    ax.add_patch(Circle((0,23),28,fc='#d5d9df',ec=BLUE,lw=2))
    ax.add_patch(Circle((-105,6),11,fc='#e6e9ec',ec=BLUE))
    rect(ax,88,6,30,27,'C','#ffe1c9')
    ax.plot([75,102,102],[33,33,33],color=BLUE,lw=3)
    arrow(ax,(103,7),(103,-3))
    ax.text(85,-21,'h: lens-to-floor gap',fontsize=9)
    arrow(ax,(60,75),(140,75),'Forward')
    ax.text(-145,89,'SIDE',weight='bold',color=TEAL)
    ax=diagram_axes(fig,[.075,.345,.85,.22]);ax.set_xlim(-145,145);ax.set_ylim(-15,100)
    ax.plot([-140,140],[0,0],color='#666666')
    rect(ax,-62,25,124,10,'Frame')
    rect(ax,-45,35,90,45,'EV3')
    rect(ax,-92,0,20,55,'R','#d5d9df');rect(ax,72,0,20,55,'L','#d5d9df')
    rect(ax,48,48,18,20,'G','#cbe9dd')
    arrow(ax,(57,70),(57,95),'Gyro sensing axis')
    ax.text(-135,85,'FRONT',weight='bold',color=TEAL)
    block(fig,.295,'Mounting checks',
      'Both driven tires must rest on the floor without chassis twist. The caster must roll '
      'freely and cross tile seams without lifting a driven wheel. Leave clearance so wheels '
      'do not rub axles, beams, cables, or sensor brackets.\n'
      'Orient the gyro to measure yaw (turning about vertical); follow the official module. '
      'The case position in this drawing does not define its internal sensing-axis orientation. '
      'A hand-rotation test must confirm it.\n'
      'Mount the color lens perpendicular and close to the floor without touching it. Try a '
      '5-10 mm lens gap as an experimental starting range, then adjust using real readings and '
      'seam clearance. This range is a tuning suggestion, not a LEGO specification.')
    save(pdf,fig,'02-side-front.svg')

    fig=page('03 / Assemble the driving base', 'Complete each checkpoint before adding sensors or changing geometry.')
    y=block(fig,.835,'A. Inventory and prepare',
      '1. Open the Driving Base manual from page 1 of this guide. Gather each part from its '
      'illustrated callouts. Match axle lengths using the manual guides; count beam holes.\n'
      '2. Inspect the two tires. Use a matching pair with the tires fully seated. Clean off dust '
      'and inspect for damage. Prepare a charged battery and keep that battery configuration '
      'through calibration and demonstration.')
    y=block(fig,y,'B. Build the stock base',
      '3. Follow the complete official illustrated sequence. Keep the specified motor '
      'connections, wheel supports, brick orientation, and caster geometry. Compare left and '
      'right sides after each assembly stage. Do not substitute axle lengths casually.\n'
      '4. Before fitting the wheels, check that each axle and retaining bush is seated as '
      'shown. After fitting them, check lateral play and rubbing. Do not overtighten a bush '
      'against a rotating part.\n'
      '5. Install the battery and place the base on the target floor. Press gently on each '
      'corner. Look for a lifted tire, loose joint, or twisted frame; correct the assembly '
      'before proceeding. Rocking on an uneven seam needs a separate floor test.')
    y=block(fig,y,'C. Reinforce only if necessary',
      '6. Hold the motor bodies and gently try to twist the frame. If the motor spacing changes '
      'visibly, identify the moving joint. First reseat its existing pins.\n'
      '7. If spare parts permit, add a cross-member between existing left/right frame mounting '
      'points, without shifting the stock geometry. Use two separated friction-pin connections '
      'at each end where holes permit; a single pin can act as a hinge. This is a fit-to-build '
      'modification, not a verified hole-specific instruction.\n'
      '8. Retest the wheels and caster after bracing. Reject any brace that bends the base, '
      'rubs a moving part, obstructs the battery, or extends the turning envelope unnecessarily.')
    block(fig,y,'Base acceptance checkpoint',
      '[ ] Wheels match and are seated.  [ ] No tire or axle rubbing.\n'
      '[ ] Motor/frame joints do not shift visibly under light hand load.\n'
      '[ ] Both driven tires contact the floor.  [ ] Caster moves freely.\n'
      '[ ] Brick buttons, battery access, and cable sockets remain accessible.')
    save(pdf,fig)

    fig=page('04 / Add and validate sensors', 'Integrate one module at a time; preserve a working mechanical baseline.')
    y=block(fig,.835,'D. Gyro assembly',
      '9. Build the official Gyro Sensor module using its illustrated sequence. Connect it to '
      'the driving base at the specified attachment points. The mount should be short, rigid, '
      'and secured against pivoting. Do not add a flexible mast.\n'
      '10. With motors stopped, keep the robot completely still while connecting the gyro and '
      'during startup. Read the angle and rotation rate if available. Log a stationary sample '
      'before moving. Simply setting the displayed angle to zero does not remove bias.\n'
      '11. Turn the whole base counterclockwise by approximately 90 degrees using a square. '
      'Check that the gyro measures that turn, then turn back. If the sign is opposite your '
      'robot convention, invert it once in the hardware adapter. If the rotation is barely '
      'detected, check the mount orientation and sensor mode.')
    y=block(fig,y,'E. Downward color sensor',
      '12. Build the official Color Sensor Down module. Before attaching it alongside the gyro, '
      'check for occupied holes, shared parts, cable interference, and wheel clearance. If the '
      'mounts conflict, test each official module separately first; the combined mount remains '
      'a physical integration task. Avoid improvised long cantilevers.\n'
      '13. Position the lens downwards, perpendicular to the surface. Measure the floor gap '
      'with the full robot loaded. Slowly move it over a tile seam by hand with motors off. '
      'Nothing should scrape and the bracket should not bounce.\n'
      '14. Record reflected-light values over plain floor, grout/seams, obstacle cardboard, and '
      'goal material, in actual room lighting. Test at more than one position. Use a fixed '
      'measurement mode during a run. Adjust the height only if separation or clearance is poor.')
    y=block(fig,y,'F. Secure cables and verify the combined assembly',
      '15. Route cables along beams inside the footprint. Retain them with suitable LEGO '
      'openings or clips; do not pinch them with pins. Leave slack at each connector.\n'
      '16. Roll and turn the unpowered robot by hand, then perform slow powered turns. Check '
      'for dragging cables, tire contact, caster snags, sensor vibration, and loose pins. '
      'Measure sensor offsets after the final mount is fixed.')
    y=link(fig,y,'Official gyro startup guidance',SENSOR)
    link(fig,y,'Official color sensor mounting and light guidance',LIGHT)
    save(pdf,fig)

    fig=page('05 / Wiring and sign conventions', 'Recommended project ports / these are choices, not mandatory LEGO assignments.')
    ax=diagram_axes(fig,[.10,.49,.80,.34]);ax.set_xlim(0,100);ax.set_ylim(0,80)
    rect(ax,33,18,34,44,'EV3 brick\n\nOUTPUTS A-D\nINPUTS 1-4')
    rect(ax,0,52,23,17,'Left motor\nB')
    rect(ax,77,52,23,17,'Right motor\nC')
    rect(ax,0,12,23,17,'Gyro\n2','#cbe9dd')
    rect(ax,77,12,23,17,'Color (optional)\n3','#ffe1c9')
    for xs,ys in [([23,33],[60,55]),([67,77],[55,60]),([23,33],[20,25]),([67,77],[25,20])]:
      ax.plot(xs,ys,color=TEAL,lw=2)
    y=block(fig,.455,'Connection map',
      'B = left large motor; C = right large motor; 2 = gyro; 3 = optional color sensor. '
      'Left and right mean as seen from behind the robot, looking forward. If your official '
      'assembly is already cabled differently, either move the cables or change the project '
      'configuration; the two must agree. Leave unused ports empty initially.')
    y=block(fig,y,'Bench test with wheels safely clear of the floor',
      '1. Command only B at low speed briefly; verify it is the left wheel. Stop it.\n'
      '2. Command only C; verify it is the right wheel. Stop it.\n'
      '3. Define positive logical speed as forward ground travel on both wheels. Mirrored '
      'motors may need opposite raw signs. Make the encoder signs match that convention too.\n'
      '4. Confirm counterclockwise physical rotation produces positive logical gyro heading.\n'
      '5. Verify the stop function and a reachable brick-button abort before floor tests.')
    block(fig,y,'Programming boundary',
      'Use the motor/sensor API permitted by the instructor. LEGO EV3 MicroPython uses '
      'Pybricks, so a blanket library ban needs clarification before choosing imports. '
      'This build does not require a prebuilt DriveBase, navigation library, or sensor-fusion '
      'package. Keep raw access and sign conversion in one hardware adapter.')
    save(pdf,fig,'03-wiring.svg')

    fig=page('06 / Geometry and calibration', 'Measure the fully assembled robot on the demonstration floor.')
    y=block(fig,.835,'Measurements to record',
      'D_L, D_R: effective wheel diameters in meters. b: lateral distance between tire contact '
      'centerlines. R: farthest horizontal distance from wheel midpoint O to any robot part. '
      's_x, s_y: color-lens offset from O, forward and left respectively. h: lens-to-floor gap.\n'
      'Use actual measurements rather than copying the normalized drawings. Keep a record '
      'of battery, floor, speed, tires, and payload so later tests are comparable.')
    y=block(fig,y,'Distance scale: calibrate forward and backward',
      'On a clear straight lane, align the robot with a square. Command a known wheel rotation '
      'at low speed and measure actual forward travel at O. Repeat at least five times and '
      'check lateral error. For n wheel rotations, D_effective = travel / (pi * n). '
      'This relation assumes a straight, nonslipping run. Exclude visibly slipping trials '
      'from scale calibration, but keep them in the reliability record.\n'
      'Use separate wheel scale factors only when repeated tests support the difference. '
      'A gyro heading controller can hide wheel mismatch, so inspect the encoder difference '
      'needed to keep straight. Do not repeatedly retune from a single run.')
    y=block(fig,y,'Odometry equations and independent checks',
      'With logical encoder changes dL and dR in degrees:\n'
      'left_distance = pi * D_L * dL / 360\n'
      'right_distance = pi * D_R * dR / 360\n'
      'ds = (left_distance + right_distance) / 2\n'
      'encoder_heading_change = (right_distance - left_distance) / b  [radians]\n'
      'For short update intervals, use ds and the midpoint heading to update x and y. Gyro '
      'heading can guide steering; compare its change with encoder heading as a consistency '
      'check. Disagreement flags possible slip or drift, but does not identify the true pose.\n'
      'Turning calibration can use b_effective = (right_distance - left_distance) / '
      'measured_heading_change, with heading in radians. Use a square or independent angle '
      'reference as well as the gyro; do not calibrate everything against one unverified sensor.')
    block(fig,y,'Sensor offset matters',
      'For robot heading theta, the lens position is:\n'
      'lens_x = x + s_x*cos(theta) - s_y*sin(theta)\n'
      'lens_y = y + s_x*sin(theta) + s_y*cos(theta)\n'
      'Use the lens position when matching a seam or goal observation to the map. A forward '
      'sensor reaching black does not mean the robot center has reached the goal center.')
    save(pdf,fig)

    fig=page('07 / Prove the error budget', 'Suggested engineering targets / these are not assignment grading requirements.')
    y=block(fig,.835,'Test 1: stationary gyro and a usable drift budget',
      'Record heading over the expected run duration while the robot remains still. Repeat '
      'startup and initialization to detect inconsistent bias. Example: 3 degrees heading '
      'error over a 1 m straight produces about 52 mm lateral error (1*sin(3 degrees)). '
      'Choose an acceptable heading error from available path clearance, not a universal '
      'threshold. A stationary test does not capture every motion-induced error.')
    y=block(fig,y,'Test 2: straight runs and turn repeatability',
      'Run ten 1 m straight trials, independently realigning before each. Record longitudinal error, '
      'lateral error, heading error, elapsed time, and visible slip. Repeat backward if the '
      'planned route uses reverse motion. Start around 0.05-0.10 m/s and tune on the floor.\n'
      'Run ten 90-degree turns in each direction. Record final physical angle, gyro angle, '
      'encoder readings, caster behavior, and any center displacement. Start around '
      '15-30 degrees/s and slow near the target. Speeds are initial tuning suggestions.\n'
      'Drive a square in both directions and measure return-to-start error. Then test a '
      'representative long route; one successful short test is not enough.')
    y=block(fig,y,'Test 3: decide whether seams are usable landmarks',
      'Sample plain tiles and seams at several locations and lighting conditions. Cross '
      'seams slowly at expected approach angles. Record missed detections and false positives. '
      'Enable corrections only if readings and mapped seam locations are consistently compatible.\n'
      'One seam observation constrains one coordinate; it does not recover full pose. '
      'Match only the expected seam within a plausible pose window, accounting for sensor '
      'offset. If two seams could explain the reading, reject the correction.\n'
      'Black cardboard and the black goal can resemble seams in reflected light. Require '
      'map context and multiple readings. Do not use obstacle crossings as landmarks: '
      'crossing obstacle tiles violates the task.')
    block(fig,y,'Clearance acceptance',
      'Let E be a conservative position-error allowance derived from repeated full-route '
      'trials, with additional reserve; a sample maximum is not a guarantee. Require planned '
      'center clearance >= R + E from obstacles and boundaries. Check every connecting segment '
      'and every turn, not just grid nodes. If no route survives this conservative model, '
      'improve the build/localization or use a more accurate footprint model; do not silently '
      'shrink clearance. Gyro plus encoders cannot detect all slip or bound position error forever.')
    save(pdf,fig)

    fig=page('08 / Start the code in stages', 'Keep each stage independently observable before combining navigation.')
    y=block(fig,.835,'Stage A: raw hardware adapter',
      'Implement read_wheel_angles(), read_heading(), optional read_reflection(), '
      'set_wheel_speeds(left, right), and stop(). Normalize signs here. Log timestamp, both '
      'encoders, gyro, reflection, requested wheel speeds, and current motion state.\n'
      'Check the stop button in every control loop, stop on exceptions with try/finally, and '
      'include motion timeouts. Detect lack of encoder progress when movement is commanded. '
      'A slip/stall abort invalidates the pose estimate: stop and physically realign before '
      'restarting unless an independent localization method has recovered pose.')
    y=block(fig,y,'Stage B: movement controller',
      'Implement turn_to_heading(target) and drive_distance(distance, target_heading). '
      'Run a timed feedback loop; begin with a simple proportional heading controller and '
      'conservative speed limits. Tune the loop period from measured I/O timing.\n'
      'Use absolute map headings, not a sequence of relative 90-degree commands. For forward '
      'motion, positive heading error means a left turn: reduce the left wheel '
      'speed and increase the right wheel speed. Slow before the endpoint, require a stable '
      'heading tolerance, and stop between moves initially. Verify behavior physically.\n'
      'Preserve the measured pose after each segment. A turn command is not proof of '
      'completion. After error-induced displacement, compute the next motion from estimated '
      'pose and check its clearance; do not blindly execute nominal lengths from the plan.')
    y=block(fig,y,'Stage C: odometry and landmarks',
      'Update pose incrementally from encoders and gyro using the measured geometry. Begin '
      'with a declared initial pose set by physical alignment. Keep the global coordinate '
      'frame consistent even if the gyro reports relative angles.\n'
      'Add seam corrections only after Test 3 passes. Only confirm the goal from black '
      'readings when the expected sensor position is near the mapped goal. Verify the '
      'required goal-arrival criterion with the instructor; the PDF does not precisely '
      'define whether the center or entire footprint must enter the goal.')
    block(fig,y,'Stage D: planning and execution',
      'Store supplied obstacle centers, start and goal in config.py. Confirm workspace '
      'dimensions: the assignment PDF contains conflicting overlaid dimensions. Build a '
      'grid and your own four-neighbor BFS first; combine collinear steps into segments.\n'
      'Inflate the 0.305 m square obstacles by the robot envelope plus error allowance, '
      'apply boundary clearance, and validate edges. Connect the exact start and goal '
      'safely to the grid. Test the planner on a laptop before executing a route. '
      'Reserve hardware.py, motion.py, odometry.py, planner.py, config.py and main.py for '
      'separate responsibilities; do not implement untested hardware assumptions in the planner.')
    save(pdf,fig)

    fig=page('Clearance and recovery decisions', 'Required before calling the assembled robot robust enough for the course.')
    y=block(fig,.835,'Compute the available error allowance',
      'For each route segment and turn, let c be the minimum distance from the planned '
      'robot center to any obstacle edge or workspace boundary. Using the conservative '
      'circular footprint, available position error A = c - R. If A <= 0, the route fails '
      'geometrically. In a centered 0.61 m straight corridor, c = 0.305 m.\n'
      'Example only: with measured R = 0.18 m, A = 0.125 m. Choosing E = 0.05 m would '
      'leave 0.075 m reserve in that straight corridor, but only if route tests support E. '
      'None of these example values are measurements of this robot.')
    y=block(fig,y,'Account for heading, distance scale, and starting error',
      'A constant heading error alpha over length L contributes L*sin(alpha) sideways '
      'error. At 2 m and 3 degrees, this is about 0.105 m. Add 0.02 m starting error and '
      'the illustrative 0.125 m allowance is almost entirely consumed.\n'
      'A 1 percent distance-scale error contributes 0.05 m over 5 m of straight travel. '
      'Gyro feedback does not remove it. Errors propagate across turns; a square that '
      'returns near its start can still have unsafe intermediate deviations.\n'
      'Measure clearance and error at intermediate checkpoints and tight turns, not just '
      'the endpoint. Include stopping overshoot, turn-center movement, and repeatable '
      'start placement in route trials. Stationary gyro drift is only one contributor.')
    y=block(fig,y,'Required adversarial route trials',
      'Use the narrowest intended corridor, longest intended straight, most turns, and '
      'a route lasting at least as long as the planned demonstration. Test both turn '
      'directions and real seam crossings. Independently replace the robot at the start '
      'each run. Repeat at realistic battery states and room lighting.\n'
      'Track all failures, including slips and false landmark detections. As a project '
      'screen, require ten consecutive full-route successes with no obstacle or boundary '
      'crossing, no manual assistance, and checkpoint error below A with chosen reserve. '
      'This is a proposed acceptance screen, not a statistical guarantee or rubric.')
    block(fig,y,'On failure: act on the measured source',
      'Slip or stall: stop, mark pose uncertain, physically realign and restart. Do not '
      'resume by zeroing encoders/gyro at the unknown location. Gyro/encoder disagreement '
      'is a warning; agreement does not prove that no slip occurred.\n'
      'Excess drift: correct startup and mount issues, compare speeds, and reduce avoidable '
      'turns/pauses. Persistent scale error: recalibrate. No clearance: shorten protrusions '
      'or replan. Poor seams: disable correction. Never force a landmark match to finish.')
    save(pdf,fig)

    fig=page('09 / Bench worksheet', 'Print this page / record the physical build before changing calibration.')
    y=block(fig,.835,'Build record',
      'Builder: __________________________  Date: __________________________\n'
      'Battery / charge condition: ________________________________________\n'
      'Floor and lighting: ________________________________________________\n'
      'Firmware and permitted hardware API: _______________________________\n'
      'Wheel description: _________________________________________________\n'
      'D_L: __________ m    D_R: __________ m    b: __________ m\n'
      'R: __________ m      s_x: __________ m    s_y: __________ m\n'
      'Lens gap h: __________ mm    Straight speed: __________ m/s\n'
      'Gyro sign: __________    Left motor sign: ____    Right motor sign: ____\n'
      'Stationary gyro duration: ______ s    Heading change: ______ degrees\n'
      'Floor reflection range: ______    Seam range: ______    Black range: ______')
    y=block(fig,y,'Repeated trial summary',
      '1 m forward: trials ____    Max forward error ____    Max lateral error ____\n'
      '90 deg left: trials ____    Max physical angle error ____\n'
      '90 deg right: trials ____   Max physical angle error ____\n'
      'Square / route test: trials ____    Largest position error ____\n'
      'Chosen planning error allowance E: ____ m    R + E: ____ m\n'
      'Seam correction enabled? ____    Evidence: ___________________________')
    y=block(fig,y,'Before each demonstration',
      '[ ] Tire seating, frame pins, caster, and sensor mounts checked.\n'
      '[ ] Battery, floor, speed, and payload match calibration.\n'
      '[ ] Course dimensions and all obstacle coordinates verified.\n'
      '[ ] Planned route and turning envelope pass clearance checks.\n'
      '[ ] Start center and heading aligned; alignment aids removed.\n'
      '[ ] Robot still during gyro initialization; stationary readings checked.\n'
      '[ ] Correct ports, stop button, timeout, and logs verified.\n'
      '[ ] Goal confirmation uses location context, not black alone.')
    block(fig,y,'Change log',
      'Modification: ______________________________________________________\n'
      'Reason / observed failure: _________________________________________\n'
      'Calibration and route tests repeated: ______________________________')
    save(pdf,fig)
  print(OUT/'ev3-build-plan.pdf')

if __name__ == '__main__':
    main()
