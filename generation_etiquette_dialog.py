# -*- coding: utf-8 -*-
"""
/***************************************************************************
 generation_etiquetteDialog
                                 A QGIS plugin
 Permet de générer les étiquettes des boites, câbles et appuis
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2023-02-20
        git sha              : $Format:%H$
        copyright            : (C) 2023 by Romain Lagrange - PCE Services
        email                : romain.lagrange@pceservices.fr
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os
import processing
import sys
import time
import pickle
import csv
import numpy as np
import unicodedata
import datetime

from PyQt5.QtCore import Qt
from qgis.PyQt import *
from qgis.core import *
from qgis.utils import iface
from PyQt5.QtWidgets import *
from PyQt5 import QtCore
from PyQt5.QtGui import * 
from PyQt5.QtCore import QVariant
from qgis.gui import QgsMapCanvas, QgsLayerTreeMapCanvasBridge
from qgis.PyQt.QtWidgets import QMessageBox
from math import *
from qgis.gui import QgsMapToolEmitPoint
from PyQt5 import QtCore
from PyQt5.QtCore import *
from PyQt5.QtWebKit import *
from PyQt5.QtWebKitWidgets import *

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'generation_etiquette_dialog_base.ui'))


class generation_etiquetteDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(generation_etiquetteDialog, self).__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        now = QDate.currentDate()
        self.dateEdit.setDate(now)

    def genererEtiquettes(self):
        for layer in QgsProject.instance().mapLayers().values():
            if 'BOITE_OPTIQUE' in layer.name():
                boitelyr = layer
                boitelyr.removeSelection()
            elif 'boite_optique' in layer.name():
                boitelyr = layer
                boitelyr.removeSelection()
            if 'CABLE_OPTIQUE' in layer.name():
                cablelyr = layer
                cablelyr.removeSelection()
            elif 'cable_optique' in layer.name():
                cablelyr = layer
                cablelyr.removeSelection()
            if 'POINT_TECHNIQUE' in layer.name():
                ptlyr = layer
                ptlyr.removeSelection()
            elif 'point_technique' in layer.name():
                ptlyr = layer
                ptlyr.removeSelection()
            if 'SUPPORT' in layer.name():
                supportlyr = layer
                supportlyr.removeSelection()
            elif 'support' in layer.name():
                supportlyr = layer
                supportlyr.removeSelection()

        datedepose = self.dateEdit.date()
        datedepose = datedepose.toString("dd/MM/yyyy")

        #Création des couches temporaires + champs
        etiquette_boite_lyr = QgsVectorLayer("Point?crs=EPSG:2154", "Etiquettes_boites", "memory")
        QgsProject.instance().addMapLayer(etiquette_boite_lyr)

        etiquette_appui_lyr = QgsVectorLayer("Point?crs=EPSG:2154", "Etiquettes_appuis", "memory")
        QgsProject.instance().addMapLayer(etiquette_appui_lyr)

        etiquette_cable_lyr = QgsVectorLayer("MultiPoint?crs=EPSG:2154", "Etiquettes_cables", "memory")
        QgsProject.instance().addMapLayer(etiquette_cable_lyr)

        etiquette_boite_lyr.startEditing()
        etiquette_appui_lyr.startEditing()
        etiquette_cable_lyr.startEditing()

        nompt = QgsField("nom pt", QVariant.String)
        Couleur = QgsField("Couleur", QVariant.String)
        Ligne1 = QgsField("Ligne1", QVariant.String)
        Ligne2 = QgsField("Ligne2", QVariant.String)
        Ligne3 = QgsField("Ligne3", QVariant.String)
        quantitefield = QgsField("Quantité", QVariant.Int)

        etiquette_boite_lyr.addAttribute(Couleur)
        etiquette_boite_lyr.addAttribute(Ligne1)
        etiquette_boite_lyr.addAttribute(Ligne2)
        etiquette_boite_lyr.addAttribute(quantitefield)
        etiquette_boite_lyr.updateFields()

        etiquette_appui_lyr.addAttribute(nompt)
        etiquette_appui_lyr.addAttribute(Couleur)
        etiquette_appui_lyr.addAttribute(Ligne1)
        etiquette_appui_lyr.addAttribute(Ligne2)
        etiquette_appui_lyr.addAttribute(Ligne3)
        etiquette_appui_lyr.addAttribute(quantitefield)
        etiquette_appui_lyr.updateFields()

        etiquette_cable_lyr.addAttribute(Couleur)
        etiquette_cable_lyr.addAttribute(Ligne1)
        etiquette_cable_lyr.addAttribute(Ligne2)
        etiquette_cable_lyr.addAttribute(Ligne3)
        etiquette_cable_lyr.addAttribute(quantitefield)
        etiquette_cable_lyr.updateFields()

        #Réparer les géométries
        parameters = { 'INPUT' : ptlyr,
            'OUTPUT' : 'TEMPORARY_OUTPUT' }
        ptoklyr = processing.run("native:deleteduplicategeometries", parameters)['OUTPUT']
        QgsProject.instance().addMapLayer(ptoklyr, False)

        parameters = { 'BEHAVIOR' : 1,
            'INPUT' : cablelyr,
            'OUTPUT' : 'TEMPORARY_OUTPUT',
            'REFERENCE_LAYER' : ptoklyr,
            'TOLERANCE' : 0.05 }
        cableoklyr = processing.run("native:snapgeometries", parameters)['OUTPUT']
        QgsProject.instance().addMapLayer(cableoklyr, False)

        parameters = { 'BEHAVIOR' : 1,
            'INPUT' : boitelyr,
            'OUTPUT' : 'TEMPORARY_OUTPUT',
            'REFERENCE_LAYER' : ptoklyr,
            'TOLERANCE' : 0.05 }
        boiteoklyr = processing.run("native:snapgeometries", parameters)['OUTPUT']
        QgsProject.instance().addMapLayer(boiteoklyr, False)

        parameters = { 'BEHAVIOR' : 1,
            'INPUT' : supportlyr,
            'OUTPUT' : 'TEMPORARY_OUTPUT',
            'REFERENCE_LAYER' : ptoklyr,
            'TOLERANCE' : 0.05 }
        supportoklyr = processing.run("native:snapgeometries", parameters)['OUTPUT']
        QgsProject.instance().addMapLayer(supportoklyr, False)

        #Etiquettes boites
        for boite in boitelyr.getFeatures():
            fet = QgsFeature()
            fet.setGeometry(boite.geometry())
            fet.setAttributes(['Blanche','ALTITUDEFIBRE39',boite["nom"],'1'])
            etiquette_boite_lyr.addFeatures([fet])
            

        #Etiquette cable
        #Créer deux étiquettes par cables par chambres
        parameters={ 'FIELD' : 'type_struc',
            'INPUT' : ptoklyr,
            'METHOD' : 0,
            'OPERATOR' : 0,
            'VALUE' : 'CHAMBRE' }
        result = processing.run("qgis:selectbyattribute", parameters)


        parameters = { 'DISCARD_NONMATCHING' : False,
            'INPUT' : QgsProcessingFeatureSourceDefinition(ptoklyr.source(), selectedFeaturesOnly=True, featureLimit=-1, geometryCheck=QgsFeatureRequest.GeometryAbortOnInvalid),
            'JOIN' : cableoklyr,
            'JOIN_FIELDS' : ['nom','capacite'],
            'METHOD' : 0,
            'OUTPUT' : 'TEMPORARY_OUTPUT',
            'PREDICATE' : [0],
            'PREFIX' : '' }
        result = processing.run("native:joinattributesbylocation", parameters)['OUTPUT']

        for pt in result.getFeatures():
            if pt["nom_2"] != NULL:
                fet = QgsFeature()
                fet.setGeometry(pt.geometry())
                fet.setAttributes(['Blanche','ALTITUDEFIBRE39',str(pt["nom_2"])+'   '+str(pt["capacite"])+' Fo', 'SRO-'+str(pt["nom_2"])[4:14]+'   '+datedepose[3:],'0'])
                etiquette_cable_lyr.addFeatures([fet])
                etiquette_cable_lyr.addFeatures([fet])


        #Créer une étiquette par pt (sauf chambre) qui touche le cable
        ptoklyr.invertSelection()


        parameters = { 'DISCARD_NONMATCHING' : False,
            'INPUT' : QgsProcessingFeatureSourceDefinition(ptoklyr.source(), selectedFeaturesOnly=True, featureLimit=-1, geometryCheck=QgsFeatureRequest.GeometryAbortOnInvalid),
            'JOIN' : cableoklyr,
            'JOIN_FIELDS' : ['nom','capacite'],
            'METHOD' : 0,
            'OUTPUT' : 'TEMPORARY_OUTPUT',
            'PREDICATE' : [3],
            'PREFIX' : '' }
        result = processing.run("native:joinattributesbylocation", parameters)['OUTPUT']


        for pt in result.getFeatures():
            if pt["nom_2"] != NULL:
                fet = QgsFeature()
                fet.setGeometry(pt.geometry())
                fet.setAttributes(['Blanche','ALTITUDEFIBRE39',str(pt["nom_2"])+'   '+str(pt["capacite"])+' Fo', 'SRO-'+str(pt["nom_2"])[4:14]+'   '+datedepose[3:],'0'])
                etiquette_cable_lyr.addFeatures([fet])


        quantitefield = etiquette_cable_lyr.fields().indexOf('Quantité')
        for cable in etiquette_cable_lyr.getFeatures():
            x=0
            valeurcherchee = str(cable["Ligne1"])+str(cable["Ligne2"])+str(cable["Ligne3"])
            for cable2 in etiquette_cable_lyr.getFeatures():
                recherche = str(cable2["Ligne1"])+str(cable2["Ligne2"])+str(cable2["Ligne3"])
                if recherche == valeurcherchee:
                    x+=1
            etiquette_cable_lyr.changeAttributeValue(cable.id(), quantitefield, x+2)


        parameters = { 'FIELD' : ['Ligne1','Ligne2','Ligne3','Quantité'],
            'INPUT' : etiquette_cable_lyr,
            'OUTPUT' : 'TEMPORARY_OUTPUT' }
        result = processing.run("native:dissolve", parameters)['OUTPUT']

        for f in etiquette_cable_lyr.getFeatures():
            etiquette_cable_lyr.deleteFeature(f.id())
        result.selectAll()
        iface.copySelectionToClipboard(result)
        iface.pasteFromClipboard(etiquette_cable_lyr)


        #Etiquette appui ORANGE et CONSTRUCTION

        parameters = { 'EXPRESSION' : "type_struc = 'APPUI' and emprise LIKE '%CONS%'",
            'INPUT' : ptoklyr,
            'OUTPUT' : 'TEMPORARY_OUTPUT' }
        result = processing.run("native:extractbyexpression", parameters)['OUTPUT']

        parameters = { 'DISCARD_NONMATCHING' : False,
            'INPUT' : result,
            'JOIN' : boiteoklyr,
            'JOIN_FIELDS' : ['code'],
            'METHOD' : 0,
            'OUTPUT' : 'TEMPORARY_OUTPUT',
            'PREDICATE' : [0],
            'PREFIX' : '' }
        result = processing.run("native:joinattributesbylocation", parameters)['OUTPUT']

        for pt in result.getFeatures():
            fet = QgsFeature()
            fet.setGeometry(pt.geometry())
            #AJOUTER LE NOM DE BOITE SI NECESSAIRE : fet.setAttributes([pt['code'],'Blanche','ALTITUDEFIBRE39',pt['code'],pt['code_2'],'1'])
            if pt['code_2'] != NULL:
                fet.setAttributes([pt['code'],'Blanche','ALTITUDEFIBRE39',pt['code'],'','1'])
            else :
                fet.setAttributes([pt['code'],'Blanche','ALTITUDEFIBRE39',pt['code'],'','1'])
            etiquette_appui_lyr.addFeatures([fet])
                
        parameters = { 'DISCARD_NONMATCHING' : True,
            'INPUT' : boiteoklyr,
            'JOIN' : ptoklyr,
            'JOIN_FIELDS' : ['code','gestionnai','emprise','type_struc'],
            'METHOD' : 0,
            'OUTPUT' : 'TEMPORARY_OUTPUT',
            'PREDICATE' : [0],
            'PREFIX' : '' }
        result = processing.run("native:joinattributesbylocation", parameters)['OUTPUT']

        parameters = { 'DISCARD_NONMATCHING' : True,
            'INPUT' : result,
            'JOIN' : cableoklyr,
            'JOIN_FIELDS' : ['capacite'],
            'OUTPUT' : 'TEMPORARY_OUTPUT',
            'PREDICATE' : [0],
            'SUMMARIES' : [3] }
        result = processing.run("qgis:joinbylocationsummary", parameters)['OUTPUT']

        for boite in result.getFeatures():
            if boite["gestionnai_2"] == 'ORANGE' and  boite["type_struc_2"] == 'APPUI'and boite['code_2'] != NULL:
                fet = QgsFeature()
                fet.setGeometry(boite.geometry())
                fet.setAttributes([boite['code_2'],'Blanche','ALTITUDEFIBRE39','SRO-'+str(boite["nom"])[4:14]+'   '+str(int(boite["capacite_max"]))+' Fo','','1'])
                etiquette_appui_lyr.addFeatures([fet])

        ptoklyr.removeSelection()
        parameters={ 'FIELD' : 'type_struc',
            'INPUT' : ptoklyr,
            'METHOD' : 0,
            'OPERATOR' : 0,
            'VALUE' : 'CHAMBRE' }
        result = processing.run("qgis:selectbyattribute", parameters)

        parameters = { 'INPUT' : supportoklyr,
            'INTERSECT' : QgsProcessingFeatureSourceDefinition(ptoklyr.source(), selectedFeaturesOnly=True, featureLimit=-1, geometryCheck=QgsFeatureRequest.GeometryAbortOnInvalid),
            'METHOD' : 0,
            'PREDICATE' : [0] }
        result = processing.run("qgis:selectbylocation", parameters)
        ptoklyr.removeSelection()


        parameters = { 'INPUT' : ptoklyr,
            'INTERSECT' : QgsProcessingFeatureSourceDefinition(supportoklyr.source(), selectedFeaturesOnly=True, featureLimit=-1, geometryCheck=QgsFeatureRequest.GeometryAbortOnInvalid),
            'METHOD' : 0,
            'PREDICATE' : [0] }
        result = processing.run("qgis:selectbylocation", parameters)

        parameters = { 'FIELD' : 'type_struc', 'INPUT' : QgsProcessingFeatureSourceDefinition(ptoklyr.source(), selectedFeaturesOnly=True, featureLimit=-1, geometryCheck=QgsFeatureRequest.GeometryAbortOnInvalid),
            'OPERATOR' : 0,
            'OUTPUT' : 'TEMPORARY_OUTPUT',
            'VALUE' : 'APPUI' }
        result = processing.run("native:extractbyattribute", parameters)['OUTPUT']

        parameters = { 'DISCARD_NONMATCHING' : True,
            'INPUT' : result,
            'JOIN' : cableoklyr,
            'JOIN_FIELDS' : ['code','capacite'],
            'OUTPUT' : 'TEMPORARY_OUTPUT',
            'PREDICATE' : [0],
            'SUMMARIES' : [3] }
        result = processing.run("qgis:joinbylocationsummary", parameters)['OUTPUT']

        for pt in result.getFeatures():
            if pt["gestionnai"] == 'ORANGE':
                fet = QgsFeature()
                fet.setGeometry(pt.geometry())
                fet.setAttributes([pt["code"],'Blanche','ALTITUDEFIBRE39','SRO-'+str(pt["code_max"])[4:14]+'   '+str(int(pt["capacite_max"]))+' Fo','','1'])
                etiquette_appui_lyr.addFeatures([fet])

        parameters = { 'INPUT' : etiquette_appui_lyr,
        'OUTPUT' : 'TEMPORARY_OUTPUT' }
        result = processing.run("native:deleteduplicategeometries", parameters)['OUTPUT']

        for f in etiquette_appui_lyr.getFeatures():
            etiquette_appui_lyr.deleteFeature(f.id())
        result.selectAll()
        iface.copySelectionToClipboard(result)
        iface.pasteFromClipboard(etiquette_appui_lyr)

        QgsProject.instance().removeMapLayers([ptoklyr.id()])
        QgsProject.instance().removeMapLayers([cableoklyr.id()])
        QgsProject.instance().removeMapLayers([boiteoklyr.id()])
        QgsProject.instance().removeMapLayers([supportoklyr.id()])
        etiquette_boite_lyr.commitChanges()
        etiquette_boite_lyr.removeSelection()
        etiquette_appui_lyr.commitChanges()
        etiquette_appui_lyr.removeSelection()
        etiquette_cable_lyr.commitChanges()
        etiquette_cable_lyr.removeSelection()