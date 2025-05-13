<?xml version="1.0" encoding="UTF-8"?>
<tileset version="1.10" tiledversion="1.11.2" name="Object" tilewidth="16" tileheight="16" spacing="1" tilecount="25" columns="5">
 <image source="../tiles/Objects.png" width="84" height="84"/>
 <tile id="15" probability="0.2">
  <animation>
   <frame tileid="15" duration="300"/>
   <frame tileid="16" duration="300"/>
  </animation>
 </tile>
 <tile id="16" probability="0.2"/>
 <tile id="17" probability="0.5">
  <animation>
   <frame tileid="17" duration="300"/>
   <frame tileid="18" duration="300"/>
  </animation>
 </tile>
 <tile id="18" probability="0.5"/>
 <tile id="20" probability="0.3">
  <animation>
   <frame tileid="20" duration="300"/>
   <frame tileid="21" duration="300"/>
  </animation>
 </tile>
 <tile id="21" probability="0.3"/>
 <wangsets>
  <wangset name="Flower" type="corner" tile="-1">
   <wangcolor name="" color="#ff0000" tile="-1" probability="1"/>
   <wangtile tileid="15" wangid="0,1,0,1,0,1,0,1"/>
   <wangtile tileid="17" wangid="0,1,0,1,0,1,0,1"/>
   <wangtile tileid="20" wangid="0,1,0,1,0,1,0,1"/>
  </wangset>
 </wangsets>
</tileset>
