"""Create exact center-crop/profile previews; no artwork or text generation."""
import argparse
import json
from pathlib import Path

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image',type=Path)
    parser.add_argument('--out-dir',type=Path,required=True)
    parser.add_argument('--title-box',type=float,nargs=4,metavar=('X0','Y0','X1','Y1'))
    args=parser.parse_args()
    try:
        from PIL import Image,ImageOps,ImageDraw
    except ImportError:
        parser.exit(2,'Optional framing preview requires Pillow or an equivalent image crop tool.\n')
    im=ImageOps.exif_transpose(Image.open(args.image)).convert('RGB')
    w,h=im.size;crop_h=min(h,round(w*4/3));crop_w=min(w,round(crop_h*3/4))
    left=(w-crop_w)//2;top=(h-crop_h)//2;box=(left,top,left+crop_w,top+crop_h)
    preview=im.crop(box);args.out_dir.mkdir(parents=True,exist_ok=True)
    preview.save(args.out_dir/'profile-3x4.png')
    thumb=preview.resize((320,427),Image.Resampling.LANCZOS);thumb.save(args.out_dir/'profile-thumbnail.png')
    diagnostic=thumb.copy();d=ImageDraw.Draw(diagnostic,'RGBA')
    d.rectangle((0,round(427*.9),round(320*.65),426),fill=(220,30,30,55),outline=(220,30,30,180))
    diagnostic.save(args.out_dir/'profile-overlay-check.png')
    report={'source_size':[w,h],'upload_matches_default_1080x1440':(w,h)==(1080,1440),'profile_crop_box':list(box),'profile_size':list(preview.size),'thumbnail_size':[320,427],'overlay_guard_in_profile':[0,.9,.65,1],'basis':'user account screenshot observation; current publisher preview takes precedence'}
    if args.title_box:
        x0,y0,x1,y1=args.title_box
        if not (0<=x0<x1<=1 and 0<=y0<y1<=1):parser.error('title-box must be ordered normalized coordinates')
        px=[x0*w,y0*h,x1*w,y1*h]
        report['title_box_pixels']=px
        report['title_inside_profile']=(px[0]>=box[0] and px[1]>=box[1] and px[2]<=box[2] and px[3]<=box[3])
        guard=[box[0],box[1]+crop_h*.9,box[0]+crop_w*.65,box[3]]
        report['title_overlaps_overlay_guard']=(px[0]<guard[2] and px[2]>guard[0] and px[1]<guard[3] and px[3]>guard[1])
    (args.out_dir/'framing-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
