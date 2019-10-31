##########################Training Samples Tool##########################

#This tool creates ranodm training samples from an input raster, with the 
#The output is in the form of a shapefile, with each point in polygon format
#for compatability with ArcPro's Image Classification Wizard. 
#The tool will only work with raster files that have a square or rectangular extent
#Zoom in to see point results, as the features are quite small. 

##########################################################################


#import all processing
from qgis.utils import iface
from qgis.PyQt.QtCore import QCoreApplication
import ogr
from qgis.core import (QgsProcessing,
                       QgsRasterLayer,
                       QgsRaster,
                       QgsFields,
                       QgsProcessingParameterRasterLayer,
                       QgsField,
                       QgsFeature,
                       QgsGeometry,
                       QgsFeatureRequest,
                       QgsProject,
                       QgsRaster,
                       QgsRectangle,
                       QgsVectorFileWriter,
                       QgsVectorLayer,
                       QgsWkbTypes,
                       QgsProcessingAlgorithm,
                       QgsProcessingException,
                       QgsProcessingOutputNumber,
                       QgsProcessingParameterDistance,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterVectorDestination,
                       QgsProcessingParameterRasterDestination)

import processing
import os




class RandomTrainingSamplesAlgorithm(QgsProcessingAlgorithm):
    """
    """
    #Set constants to be called upon later
    
    INPUT = 'INPUT'
    OUTPUT = 'OUTPUT'
    DISTANCE_BETWEEN_POINTS = 'DISTANCE_BETWEEN_POINTS'
    NUMBER_OF_POINTS = 'NUMBER_OF_POINTS'
    
    

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        # Returns algorithm
        return RandomTrainingSamplesAlgorithm()

    def name(self):
        """
        Returns the unique algorithm name.
        """
        return 'random_training_samples'

    def displayName(self):
        """
        Returns the translated algorithm name.
        """
        return self.tr('Training Samples Generator')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to.
        """
        return self.tr('Example scripts')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs
        to.
        """
        return 'examplescripts'

    def shortHelpString(self):
        """
        Returns a localised short help string for the algorithm.
        """
        return self.tr('Creates random training sample data from an input raster. Number of samples and distance between samples can be specified. The output is in polygon format, for compatibility with ArcGIS machine learning classifiers. Distance input is float and Number of points is integer. Input raster should be single band and classified. The output will be named as specified in filepath, but appear as Buffered if output file after running algorithm is selected.')
    
    #This section sets the project parameters
    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and outputs of the algorithm.
        """
        # Main input raster
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.INPUT,
                self.tr('Input Raster layer'),
            )
        )
        # Project Output
        self.addParameter(
            QgsProcessingParameterVectorDestination(
                self.OUTPUT,
                self.tr('Training Samples')
            )
        )
        #Input for distance between points
        self.addParameter(
            QgsProcessingParameterDistance(
                self.DISTANCE_BETWEEN_POINTS,
                self.tr('DISTANCE_BETWEEN_POINTS'),
                defaultValue = 0.1,
                # Make distance units match the INPUT layer units:
                parentParameterName='INPUT'
            )
        )
        #Input for number of points
        self.addParameter(
            QgsProcessingParameterDistance(
                self.NUMBER_OF_POINTS,
                self.tr('NUMBER_OF_POINTS'),
                defaultValue = 100.0,
                parentParameterName='INPUT'
            )
        )
    #This sections defines the new processing parameter
    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        filepath = '/Users/simonharrington/Documents/Year_4/Geospatial_Programming/Module_5/'
        
        #Create layer extent from input raster. This is due to a polygon input being needed for the next step.
        raster_2_poly = processing.run(
            'qgis:polygonfromlayerextent',
            {
                #Original parameter values of INPUT into the polygon from layer extent algorithm.
                'INPUT': parameters[self.INPUT],
                'OUTPUT': 'memory:',
            },
            # It's important to pass on the context and feedback objects to
            # child algorithms, so that they can properly give feedback to
            # users and handle cancelation requests.
            # Because the buffer algorithm is being run as a step in
            # another larger algorithm, the is_child_algorithm option
            #should be set to True
            is_child_algorithm=True,
            #
            # It's important to pass on the context and feedback objects to
            # child algorithms, so that they can properly give feedback to
            # users and handle cancelation requests.
            context=context,
            feedback=feedback)

        # Check for cancelation
        if feedback.isCanceled():
            return {}

        #Generate random points within the bounds of the input raster, with the amount and distance specified by the user
        random_points = processing.run(
            'qgis:randompointsinlayerbounds',
            {
                # Input as boundary from raster_2_poly
                'INPUT': raster_2_poly['OUTPUT'],
                'MIN_DISTANCE': parameters[self.DISTANCE_BETWEEN_POINTS],
                'OUTPUT': 'memory:',
                'POINTS_NUMBER': parameters[self.NUMBER_OF_POINTS],
            },
            is_child_algorithm=True,
            context=context,
            feedback=feedback)

        if feedback.isCanceled():
            return {}
        
        #Extracts values from raster, adding them to a point layer
        value_points = processing.run(
            'saga:addrastervaluestopoints',
            {
                # Here we pass the 'OUTPUT' value from the buffer's result
                # dictionary off to the rasterize child algorithm.
                'SHAPES': random_points['OUTPUT'],
                'GRIDS': parameters[self.INPUT],
                # Use the original parameter value.
                'RESAMPLING':0,
                'RESULT': filepath + 'value_points.shp',
            },
            is_child_algorithm=True,
            context=context,
            feedback=feedback)

        if feedback.isCanceled():
            return {}
        #Buffer points layer with extracted values, to convert to polygon.
        buffer_points = processing.run(
            'native:buffer',
            {
                'INPUT': value_points['RESULT'],
                'OUTPUT': parameters[self.OUTPUT],
                'DISTANCE': 10,
                'SEGMENTS': 10,
                'DISSOLVE': False,
                'END_CAP_STYLE': 0,
                'JOIN_STYLE': 0,
                'MITER_LIMIT': 2,
            },
            is_child_algorithm=True,
            context=context,
            feedback=feedback)
        #Delete file made for value_points step. 
        os.remove(filepath + 'value_points.shp')
        os.remove(filepath + 'value_points.shx')
        os.remove(filepath + 'value_points.prj')
        os.remove(filepath + 'value_points.dbf')
        os.remove(filepath + 'value_points.mshp')
        # Return the results
        return {'OUTPUT': buffer_points['OUTPUT'],
                }