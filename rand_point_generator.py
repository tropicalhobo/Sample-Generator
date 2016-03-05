   #create vector points
    drvr = ogr.GetDriverByName('ESRI Shapefile')

    ds = drvr.CreateDataSource('random_sample_test.shp')

    layer = ds.CreateLayer('random_sample_test', geom_type=ogr.wkbPoint)

    if os.path.exists('random_sample_test.shp'):
        pass

    #add fields to layers
    field_defn = ogr.FieldDefn('map_coord',ogr.OFTReal)

    layer.CreateField(field_defn)

    #add features
    feat_defn = layer.GetLayerDefn()
    feature = ogr.Feature(feat_defn)

    #set geometry of new feature
    feat = feature.SetGeometry(point)

    feat.SetField('map_coord',)